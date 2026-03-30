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

// ========== 核心逻辑 ==========

/**
 * 获取套餐完整信息
 * @param {string[]} itemIds - 项目ID数组，如 ['Item029', 'Item035']
 * @returns {{ items: Object[], totalPrice: number, shortCode: string }}
 */
function buildPackage(itemIds = []) {
  // 合并必选项
  const allIds = [...new Set([...MANDATORY, ...itemIds])];

  const items = allIds.map(id => {
    const info = ITEMS_DB[id];
    if (!info) return null;
    return { id, name: info.name, price: info.price, mandatory: MANDATORY.includes(id) };
  }).filter(Boolean);

  const totalPrice = items.reduce((sum, it) => sum + (it.price || 0), 0);
  const shortCode = `HL-${Date.now().toString(36).toUpperCase().slice(-6)}`;

  return { items, totalPrice, shortCode };
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
  const { items, totalPrice, shortCode } = pkg;

  const itemLines = items.map(it =>
    `${it.mandatory ? '⭐' : '　'} ${it.id} ${it.name} ${it.price > 0 ? `¥${it.price}` : '免费'}`
  ).join('\n');

  return `体检套餐预约
━━━━━━━━━━━━━━━━━━━━
📋 套餐清单（共${items.length}项，含必选常规检查）

${itemLines}

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
async function generateQR(outputPath, itemIds = []) {
  if (!outputPath) {
    outputPath = path.join(__dirname, '..', '体检预约二维码.png');
  }
  outputPath = path.resolve(outputPath);

  const pkg = buildPackage(itemIds);
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
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('用法: node generate_qr.js [output_path] [ItemID1] [ItemID2] ...');
    console.log('示例: node generate_qr.js output.png Item029 Item035 Item128 Item036');
    console.log('');
    console.log('--- 演示模式（含必选 Item029）---');
    const demoIds = ['Item035', 'Item128', 'Item036']; // 不含Item029，但会自动加上
    const pkg = buildPackage(demoIds);
    console.log(`\n套餐：${pkg.items.length}项，总价：¥${pkg.totalPrice}`);
    console.log('清单：');
    pkg.items.forEach(it => console.log(`  ${it.id} ${it.name} ¥${it.price}`));
    generateQR(path.join(__dirname, '..', '体检预约_demo.png'), demoIds)
      .catch(e => { console.error(e); process.exit(1); });
    return;
  }

  const outputPath = args[0];
  const itemIds = args.slice(1).filter(a => a.startsWith('Item'));

  if (itemIds.length === 0) {
    console.error('[ERROR] 请至少指定一个 ItemID');
    process.exit(1);
  }

  generateQR(outputPath, itemIds).catch(e => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { buildPackage, buildQRContent, generateQR };
