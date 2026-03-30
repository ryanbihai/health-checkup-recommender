#!/usr/bin/env node
/**
 * 体检项目核查脚本（支持 ItemID + 中文名双模式）
 *
 * 1. ItemID 直接通过（Item029、Item128 等）
 * 2. 中文名模糊匹配（"胃镜"、"颈动脉彩超"等）
 * 3. 旧编码兼容（HLZXX0205 等，仍从 md 文件读取）
 *
 * 用法: node verify_items.js Item029 胃镜 Item128
 */

const fs = require('fs');
const path = require('path');

const ITEMS_JSON_PATH = path.join(__dirname, '..', 'reference', 'checkup_items.json');
const ITEMS_MD_PATH   = path.join(__dirname, '..', 'reference', 'checkup_items.md');

let ITEMS_DB = {};        // id -> { name, price }
let NAME_TO_ID = {};      // normalized name -> id

try {
  const data = JSON.parse(fs.readFileSync(ITEMS_JSON_PATH, 'utf-8'));
  ITEMS_DB = data.items || {};
  // 构建中文名反向索引
  for (const [id, info] of Object.entries(ITEMS_DB)) {
    const key = info.name.replace(/\s+/g, ' ').trim().toLowerCase();
    NAME_TO_ID[key] = id;
  }
} catch (e) {
  console.error('[WARN] 无法加载 checkup_items.json:', e.message);
}

// 从 md 文件加载旧编码（兼容）
let OLD_CODE_MAP = {}; // name -> HLZXX code
try {
  const md = fs.readFileSync(ITEMS_JSON_PATH.replace('.json', '.md'), 'utf-8');
  const rows = md.match(/^\|\s*HLZXX[\d~\-A-Z]+\s*\|\s*([^|]+?)\s*\|/gm) || [];
  for (const row of rows) {
    const parts = row.split('|');
    const code = parts[1]?.trim();
    const name = parts[2]?.trim();
    if (code && name) OLD_CODE_MAP[name.toLowerCase()] = code;
  }
} catch (e) {
  // md 不存在没关系
}

function normalize(str) {
  return str.trim().replace(/\s+/g, ' ');
}

/**
 * 验证单个项目
 * @returns {{ id, name, price, status, from }}
 */
function verifyOne(item) {
  const norm = normalize(item);

  // 1. 精确 ItemID
  if (norm in ITEMS_DB) {
    return { id: norm, name: ITEMS_DB[norm].name, price: ITEMS_DB[norm].price, status: '✅', from: 'ItemID' };
  }

  // 2. 大小写不敏感 ItemID（item029 → Item029）
  const lowerId = 'item' + norm.replace(/^item/i, '');
  if (lowerId in ITEMS_DB) {
    return { id: lowerId, name: ITEMS_DB[lowerId].name, price: ITEMS_DB[lowerId].price, status: '✅', from: 'ItemID' };
  }

  // 3. 中文名模糊匹配
  const normLower = norm.toLowerCase();
  for (const [key, id] of Object.entries(NAME_TO_ID)) {
    if (key.includes(normLower) || normLower.includes(key)) {
      return { id, name: ITEMS_DB[id].name, price: ITEMS_DB[id].price, status: '✅', from: '中文名匹配' };
    }
  }

  // 4. 旧编码（HLZXX...）
  if (norm.startsWith('HLZXX') && Object.values(OLD_CODE_MAP).includes(norm)) {
    const name = Object.entries(OLD_CODE_MAP).find(([, v]) => v === norm)?.[0];
    const id = Object.entries(ITEMS_DB).find(([, v]) => v.name.toLowerCase() === name)?.[0];
    if (id) return { id, name: ITEMS_DB[id].name, price: ITEMS_DB[id].price, status: '✅', from: '旧编码' };
  }

  return { item: norm, status: '❌', hint: '未找到对应项目，请检查 ID 或中文名称' };
}

/**
 * 批量验证
 * @param {string[]} items - 项目列表（ItemID 或中文名）
 * @returns {{ results, errors, totalPrice }}
 */
function verify(items) {
  const results = [];
  const errors = [];

  for (const item of items) {
    const r = verifyOne(item);
    if (r.status === '✅') {
      results.push(r);
    } else {
      errors.push(r);
    }
  }

  const totalPrice = results.reduce((s, r) => s + (r.price || 0), 0);
  return { results, errors, totalPrice };
}

// CLI
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('用法: node verify_items.js Item029 Item035 胃镜 颈动脉彩超');
    console.log('示例: node verify_items.js Item128 Item035');
    console.log('');
    console.log('支持格式: ItemID (Item029) / 中文名 (胃镜) / 旧编码 (HLZXX0205)');
    process.exit(1);
  }

  const { results, errors, totalPrice } = verify(args);

  console.log('\n🔍 体检项目核查结果\n');
  console.log('━━━ 有效项目 ━━━');
  results.forEach(r => {
    console.log(`${r.status} ${r.id}  ${r.name}  ¥${r.price}  [${r.from}]`);
  });

  if (errors.length > 0) {
    console.log('\n━━━ 疑似问题项目 ━━━');
    errors.forEach(e => {
      console.log(`${e.status} ${e.item}`);
      if (e.hint) console.log(`   → ${e.hint}`);
    });
  }

  console.log(`\n✅ 有效: ${results.length}  ❌ 无效: ${errors.length}`);
  if (results.length > 0) {
    console.log(`💰 合计价格: ¥${totalPrice}（仅供参考，以医院实际收费为准）`);
  }

  if (errors.length > 0) process.exit(1);
}

module.exports = { verify, verifyOne, ITEMS_DB };
