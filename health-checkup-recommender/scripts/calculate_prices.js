#!/usr/bin/env node
/**
 * 价格计算器 - 计算体检套餐总价
 *
 * 设计原则：价格计算必须由代码完成，禁止 LLM 手动计算！
 *
 * 用法:
 *   node calculate_prices.js Item029 Item131 Item173
 *
 * 或在代码中调用:
 *   const { calculateTotal, getPriceInfo } = require('./calculate_prices.js');
 *   const result = calculateTotal(['item029', 'item131', 'item173']);
 *   console.log(result.total); // 输出总价
 */

const fs = require('fs');
const path = require('path');
const { checkConflicts } = require('./check_conflicts.js');

const ITEMS_JSON_PATH = path.join(__dirname, '..', 'reference', 'checkup_items.json');
let ITEMS_DB = {};

try {
  const data = JSON.parse(fs.readFileSync(ITEMS_JSON_PATH, 'utf-8'));
  ITEMS_DB = data.items || {};
} catch (e) {
  console.error('[ERROR] 无法加载 checkup_items.json:', e.message);
  process.exit(1);
}

/**
 * 获取单个项目的价格信息
 * @param {string} itemId - 项目ID（如 'item029' 或 'Item029'）
 * @returns {{ id, name, price } | null}
 */
function getPriceInfo(itemId) {
  const norm = itemId.trim().toLowerCase();
  const key = norm.startsWith('item') ? norm : `item${norm}`;

  if (ITEMS_DB[key]) {
    return {
      id: key,
      name: ITEMS_DB[key].name,
      price: ITEMS_DB[key].price
    };
  }
  return null;
}

/**
 * 计算套餐总价（自动处理冲突去重）
 * @param {string[]} itemIds - 项目ID数组
 * @returns {{ total: number, items: Array, count: number, breakdown: string }}
 */
function calculateTotal(itemIds) {
  if (!Array.isArray(itemIds) || itemIds.length === 0) {
    return { total: 0, items: [], count: 0, breakdown: '' };
  }

  // 使用 checkConflicts 进行冲突检测和去重
  const { resolved, removed, total } = checkConflicts(itemIds);

  // 获取详细信息
  const items = resolved.map(id => {
    const info = getPriceInfo(id);
    return info || { id, name: '未知', price: 0 };
  });

  // 生成详细的价格明细
  const breakdown = items.map(item =>
    `  - ${item.id} ${item.name} ¥${item.price}`
  ).join('\n');

  return {
    total,
    items,
    count: items.length,
    breakdown,
    removed: removed.map(r => ({
      id: r.id,
      name: r.name,
      reason: r.reason
    }))
  };
}

/**
 * 格式化输出（供 LLM 直接使用）
 * @param {string[]} itemIds
 * @returns {string}
 */
function formatOutput(itemIds) {
  const result = calculateTotal(itemIds);

  let output = '\n💰 【价格计算结果】\n\n';
  output += `📋 项目明细（共 ${result.count} 项）：\n`;
  output += result.breakdown + '\n\n';

  if (result.removed && result.removed.length > 0) {
    output += `⚠️ 冲突去重（已自动移除 ${result.removed.length} 项）：\n`;
    result.removed.forEach(r => {
      output += `  ❌ ${r.id} ${r.name}\n    → ${r.reason}\n`;
    });
    output += '\n';
  }

  output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
  output += `💵 套餐总价：¥${result.total}\n`;
  output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
  output += `✅ 验证通过，共 ${result.count} 项\n`;
  output += `（仅供参考，以医院实际收费为准）\n`;

  return output;
}

// CLI 入口
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('\n📌 用法:');
    console.log('  node calculate_prices.js Item029 Item131 Item173 Item032');
    console.log('\n💡 演示:');
    const demo = ['Item029', 'Item131', 'Item173', 'Item032', 'Item154', 'Item035'];
    console.log(`  输入: ${demo.join(', ')}\n`);
    console.log(formatOutput(demo));
    process.exit(0);
    return;
  }

  console.log(formatOutput(args));
}

// 导出函数供其他模块使用
module.exports = {
  getPriceInfo,
  calculateTotal,
  formatOutput,
  ITEMS_DB
};
