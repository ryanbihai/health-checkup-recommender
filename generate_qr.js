/**
 * generate_qr.js - 体检预约二维码生成脚本（价格版 v3.0）
 *
 * ⚠️ 安全设计原则：
 * - 二维码不含任何可识别PII
 * - 不向第三方URL传递用户数据
 * - Item029（常规检查1）为必选项，自动加入
 *
 * 使用方式：
 *   node scripts/generate_qr.js <output_path> [ItemID1] [ItemID2] ...
 *   示例：node scripts/generate_qr.js output.png Item029 Item035 Item128
 *
 * 数据来源：reference/checkup_items.json
 */

const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');

const ITEMS_FILE = path.join(__dirname, '..', 'reference', 'checkup_items.json');

// ========== 加载项目数据 ==========
let ITEMS_DB = {};
let MANDATORY = [];

try {
  const raw = fs.readFileSync(ITEMS_FILE, 'utf-8');
  const data = JSON.parse(raw);
  ITEMS_DB = data.items || {};
  MANDATORY = data.mandatory || ['Item029'];
} catch (e) {
  console.error('[ERROR] 无法加载 checkup_items.json:', e.message);
  process.exit(1);
}

// ========== 套餐编码表（用于摘要） ==========
const ITEMS_MAP = {
  '胃镜': 'G01', '肠镜': 'G02', '低剂量螺旋CT': 'G03',
  '前列腺特异抗原': 'G04', '心脏彩超': 'G05', '同型半胱氨酸': 'G06',
  '肝纤维化检测': 'G07', '糖化血红蛋白': 'G08', '颈动脉彩超': 'G09',
  '冠状动脉钙化积分': 'G10', '乳腺彩超+钼靶': 'G11', 'TCT+HPV': 'G12',
};

const { checkConflicts } = require('./check_conflicts.js');

// ========== 核心逻辑 ==========

/**
 * 获取套餐完整信息（含保底400自动补充）
 * @param {string[]} itemIds - 项目ID数组，如 ['Item029', 'Item035']
 * @param {Object} userProfile - { age, gender, healthConditions[] }
 * @returns {{ items, totalPrice, shortCode, addedByTopup, topupReason }}
 */
function buildPackage(itemIds = [], userProfile = {}) {
  // 合并必选项
  const baseIds = [...new Set([...MANDATORY, ...itemIds])];
  const baseItems = baseIds.map(id => {
    const info = ITEMS_DB[id];
    if (!info) return null;
    return { id, name: info.name, price: info.price || 0, mandatory: MANDATORY.includes(id) };
  }).filter(Boolean);
  const baseTotal = baseItems.reduce((s, it) => s + it.price, 0);

  // 保底400自动补充
  // 冲突检测：父子项去重（保留父项，移除子项）
  const { resolved: conflictFreeIds } = checkConflicts(baseIds);

  const { addedIds, reason: topupReason } = autoTopup(baseTotal, conflictFreeIds, userProfile);
  const allIds = [...new Set([...conflictFreeIds, ...addedIds])];

  const items = allIds.map(id => {
    const info = ITEMS_DB[id];
    if (!info) return null;
    return {
      id,
      name: info.name,
      price: info.price || 0,
      mandatory: MANDATORY.includes(id),
      topup: addedIds.includes(id),
    };
  }).filter(Boolean);

  const totalPrice = items.reduce((s, it) => s + it.price, 0);
  const shortCode = `HL-${Date.now().toString(36).toUpperCase().slice(-6)}`;

  return { items, totalPrice, shortCode, addedByTopup: addedIds, topupReason };
}

// ========== 保底 ¥400 自动补充逻辑 ==========

/**
 * 根据用户画像（年龄/性别/健康状况）自动补充套餐至 ¥400
 * @param {number} currentTotal - 当前套餐总价
 * @param {string[]} currentIds - 当前已有的项目ID
 * @param {Object} userProfile - { age, gender, healthConditions[] }
 * @returns {{ addedIds: string[], reason: string }}
 */
function autoTopup(currentTotal, currentIds, userProfile = {}) {
  const { age = 50, gender = 'M', healthConditions = [] } = userProfile;
  const deficit = 400 - currentTotal;
  if (deficit <= 0) return { addedIds: [], reason: '' };

  const added = [];
  const reasons = [];
  const condSet = new Set(healthConditions.map(c => c.toLowerCase()));
  const existing = new Set(currentIds);
  const inTopup = new Set(); // 本轮已补充的去重

  const candidates = [];

  const push = (id, reason) => {
    if (!existing.has(id) && !inTopup.has(id)) {
      candidates.push({ id, reason });
      inTopup.add(id);
    }
  };

  // 高血糖 → 糖化血红蛋白 + 血脂
  if (condSet.has('高血糖') || condSet.has('血糖高') || condSet.has('糖尿病')) {
    push('Item142', '高血糖：糖化血红蛋白');
    push('Item173', '高血糖：血脂四项');
    push('Item150', '高血糖：同型半胱氨酸');
  }

  // 心脑血管风险
  if (condSet.has('高血压') || condSet.has('高血脂') || condSet.has('心脑血管')) {
    push('Item150', '心脑血管风险：同型半胱氨酸');
    push('Item036', '心脑血管风险：颈动脉彩超');
    push('Item161', '心脑血管风险：心肌酶4项');
  }

  // 男性 50+ → 前列腺 + 心脑血管
  if (gender === 'M' && age >= 50) {
    push('Item128', '男性50+：前列腺特异抗原');
    push('Item037', '男性50+：前列腺彩超');
    push('Item150', '男性50+：同型半胱氨酸');
    push('Item036', '男性50+：颈动脉彩超');
  }

  // 女性 40+ → 乳腺 + 妇科
  if (gender === 'F' && age >= 40) {
    push('Item038', '女性40+：乳腺彩超');
    push('Item039', '女性40+：乳腺钼靶');
    push('Item026', '女性：宫颈TCT+白带');
  }

  // 脂肪肝/肝问题
  if (condSet.has('脂肪肝') || condSet.has('肝')) {
    push('Item083', '肝脏风险：肝功能11项');
  }

  // 50+ 吸烟/肺
  if (age >= 50 && (condSet.has('吸烟') || condSet.has('肺'))) {
    push('Item007', '肺部风险：胸部CT');
  }

  // 通用补充（按价格从低到高）
  const fallback = [
    ['Item131', '基础补充：血常规'],
    ['Item167', '基础补充：空腹血糖'],
    ['Item071', '基础补充：肝功能（ALT）'],
    ['Item138', '基础补充：尿酸'],
    ['Item173', '基础补充：血脂四项'],
    ['Item048', '基础补充：动脉硬化检测'],
    ['Item035', '基础补充：甲状腺彩超'],
    ['Item113', '基础补充：心电图'],
    ['Item174', '基础补充：血脂7项'],
  ];
  for (const [id, reason] of fallback) push(id, reason);

  // 优先级分组：
  // 0 = 高风险匹配项（优先），1 = 通用临床项，2 = 基础补项
  const priorityMap = {};
  const riskTerms = new Set(['高血糖', '糖尿病', '高血压', '高血脂', '心脑血管', '脂肪肝', '吸烟', '肺', '肝', '男性50+', '女性40+']);

  candidates.forEach(c => {
    const reasonLower = c.reason.toLowerCase();
    const isRiskMatch = Array.from(riskTerms).some(t => reasonLower.includes(t));
    priorityMap[c.id] = isRiskMatch ? 0 : (reasonLower.includes('基础补充') ? 2 : 1);
  });

  // 高风险项优先，其次按价格升序
  candidates.sort((a, b) => {
    const pa = priorityMap[a.id] ?? 1;
    const pb = priorityMap[b.id] ?? 1;
    if (pa !== pb) return pa - pb;
    return (ITEMS_DB[a.id]?.price || 0) - (ITEMS_DB[b.id]?.price || 0);
  });

  let remaining = deficit;
  const addedSet = new Set();
  for (const c of candidates) {
    if (remaining <= 0) break;
    const price = ITEMS_DB[c.id]?.price || 0;
    added.push(c.id);
    addedSet.add(c.id);
    reasons.push(c.reason);
    remaining -= price;
  }

  // 若仍不足400，补入最便宜项目（哪怕略超）
  if (remaining > 0) {
    const sortedAll = Object.keys(ITEMS_DB)
      .filter(id => !MANDATORY.includes(id) && !addedSet.has(id))
      .sort((a, b) => (ITEMS_DB[a].price || 0) - (ITEMS_DB[b].price || 0));
    for (const id of sortedAll) {
      const price = ITEMS_DB[id].price || 0;
      added.push(id);
      reasons.push('保底400：补充至服务起点价');
      remaining -= price;
      if (remaining <= 0) break;
    }
  }

  return { addedIds: added, reason: reasons.join('；') };
}

/**
 * 生成套餐摘要（用于二维码，只含ID序列不暴露信息）
 */
function encodePackage(itemIds = []) {
  const allIds = [...new Set([...MANDATORY, ...itemIds])];
  const codes = allIds.map(id => id.replace('Item', '')).join('-');
  return `HL-${Date.now().toString(36).toUpperCase().slice(-4)}-${codes}`;
}

/**
 * 生成二维码内容（含完整清单和价格）
 * @param {Object} pkg - buildPackage() 返回的套餐对象
 * @returns {string} 二维码文本内容
 */
function buildQRContent(pkg) {
  const { items, totalPrice, shortCode, addedByTopup = [], topupReason = '' } = pkg;

  const itemLines = items.map(it => {
    const flag = it.mandatory ? '⭐' : (it.topup ? '🔹' : '　');
    const price = it.price > 0 ? `¥${it.price}` : '免费';
    return `${flag} ${it.id} ${it.name} ${price}`;
  }).join('\n');

  let topupNote = '';
  if (addedByTopup.length > 0) {
    topupNote = `\n🔹 为达到服务起点价，已根据风险画像自动补充（${topupReason}）`;
  }

  return `体检套餐预约
━━━━━━━━━━━━━━━━━━━━
📋 套餐清单（共${items.length}项，含必选常规检查）

${itemLines}
${topupNote}

━━━━━━━━━━━━━━━━━━━━
💰 套餐总价：¥${totalPrice}
📌 预约码：${shortCode}
🌐 请至 www.ihaola.com.cn 出示本码
⚠️ 本码不含个人信息，请携带身份证就诊`;
}

// ========== 二维码生成 ==========

/**
 * 生成二维码图片
 * @param {string} outputPath - 输出路径
 * @param {string[]} itemIds - 项目ID数组
 */
async function generateQR(outputPath, itemIds = [], userProfile = {}) {
  if (!outputPath) {
    outputPath = path.join(__dirname, '..', '体检预约二维码.png');
  }
  outputPath = path.resolve(outputPath);

  const pkg = buildPackage(itemIds, userProfile);
  const qrContent = buildQRContent(pkg);

  const opts = {
    errorCorrectionLevel: 'M',
    type: 'image/png',
    margin: 2,
    width: 400,
    color: { dark: '#1a3a5c', light: '#ffffff' },
  };

  await QRCode.toFile(outputPath, qrContent, opts);

  const stats = fs.statSync(outputPath);
  console.log(`[OK] QR saved: ${outputPath} (${Math.round(stats.size / 1024)} KB)`);
  console.log(`\n${qrContent}`);
  return { path: outputPath, ...pkg };
}

// ========== CLI ==========
/**
 * CLI 用法：
 * node generate_qr.js [output_path] [ItemID1] [ItemID2] ... [--age N] [--gender M|F] [--cond NAME]
 * 示例：
 *   node generate_qr.js out.png Item029 Item131 --age 50 --gender M --cond 高血糖
 */
if (require.main === module) {
  const args = process.argv.slice(2);

  // 解析 --age / --gender / --cond 选项
  const userProfile = { age: 50, gender: 'M', healthConditions: [] };
  const realArgs = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--age' && args[i+1])     userProfile.age = parseInt(args[++i]);
    else if (args[i] === '--gender' && args[i+1]) userProfile.gender = args[++i].toUpperCase();
    else if (args[i] === '--cond' && args[i+1])  userProfile.healthConditions.push(args[++i]);
    else realArgs.push(args[i]);
  }

  const outputPath = realArgs[0];
  const itemIds = realArgs.slice(1).filter(a => a.startsWith('Item'));

  if (itemIds.length === 0) {
    console.log('用法: node generate_qr.js [output_path] [ItemID1] [ItemID2] ... [--age N] [--gender M|F] [--cond NAME]');
    console.log('示例: node generate_qr.js out.png Item029 --age 50 --gender M --cond 高血糖');
    console.log('');
    console.log('--- 演示模式（触发保底400自动补充）---');
    const demoIds   = ['Item029'];                          // 极简套餐 → 触发补充
    const demoProfile = { age: 50, gender: 'M', healthConditions: ['高血糖'] };
    const pkg = buildPackage(demoIds, demoProfile);
    console.log(`\n套餐：${pkg.items.length}项，总价：¥${pkg.totalPrice}`);
    if (pkg.addedByTopup.length) console.log('自动补充：', pkg.topupReason);
    pkg.items.forEach(it => console.log(`  ${it.id} ${it.name} ¥${it.price}`));
    generateQR(path.join(__dirname, '..', '体检预约_demo.png'), demoIds, demoProfile)
      .catch(e => { console.error(e); process.exit(1); });
    return;
  }

  generateQR(outputPath, itemIds, userProfile).catch(e => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { buildPackage, buildQRContent, generateQR };
