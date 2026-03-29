#!/usr/bin/env node
/**
 * 体检项目核查脚本
 * 检查推荐项目是否在 checkup_items.md 加项包中真实存在
 * 防止 AI 幻觉推荐不存在的项目
 *
 * 用法: node verify_items.js 项目1 项目2 项目3 ...
 */

const fs = require('fs');
const path = require('path');

const CHECKUP_ITEMS_PATH = path.join(__dirname, '..', 'reference', 'checkup_items.md');
const SYMPTOM_MAPPING_PATH = path.join(__dirname, '..', 'reference', 'symptom_mapping.json');

function loadCheckupItems() {
  const content = fs.readFileSync(CHECKUP_ITEMS_PATH, 'utf8');

  // 从加项包表格中提取所有项目名称和编码
  const items = new Map(); // name -> {code, from: 'core'|'addon'}

  // 匹配加项包表格行: | HLZXX0205 | 胃镜 | ...
  const addonRegex = /^\|\s*HLZXX[\d~\-A-Z]+\s*\|\s*([^|]+?)\s*\|/gm;
  let match;
  while ((match = addonRegex.exec(content)) !== null) {
    const name = match[1].trim();
    items.set(name, { code: 'addon', from: '加项包' });
  }

  // 也提取核心项目（用于判断是否已在基础套餐中）
  const coreRegex = /^\|\s*HLZXX[\d~\-A-Z]+\s*\|\s*([^|]+?)\s*\|/gm;
  // 核心项目部分（表格前面）
  const coreSection = content.match(/## 核心项目（必查）([\s\S]*?)## 加项包/);
  if (coreSection) {
    const coreContent = coreSection[1];
    let coreMatch;
    const coreRe = /^\|\s*HLZXX[\d~\-A-Z]+\s*\|\s*([^|]+?)\s*\|/gm;
    while ((coreMatch = coreRe.exec(coreContent)) !== null) {
      const name = coreMatch[1].trim();
      if (!items.has(name)) {
        items.set(name, { code: 'core', from: '基础套餐' });
      }
    }
  }

  return items;
}

function normalize(str) {
  return str.trim().replace(/\s+/g, ' ');
}

function verify(recommendedItems) {
  const validItems = loadCheckupItems();
  const results = [];
  const errors = [];

  for (const item of recommendedItems) {
    const normalized = normalize(item);
    const found = Array.from(validItems.entries()).find(([name]) =>
      normalize(name).includes(normalized) || normalized.includes(normalize(name))
    );

    if (found) {
      results.push({
        item: normalized,
        status: '✅',
        found: found[0],
        from: found[1].from
      });
    } else {
      // 模糊匹配 - 检查是否包含关键词
      const keywords = ['CT', 'MRI', '超声', '彩超', '镜', '肿瘤', '血糖', '血脂', '肝功能', '肾功能', '心电图', '血压', '骨密度'];
      const matchedKeyword = keywords.find(k => normalized.includes(k));

      errors.push({
        item: normalized,
        status: '❌',
        matchedKeyword,
        hint: '⚠️ 不在加项包中，请从 symptom_mapping.json 选取标准组合，或咨询医疗机构'
      });
    }
  }

  return { results, errors };
}

// CLI
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('用法: node verify_items.js 项目1 项目2 项目3 ...');
    console.log('示例: node verify_items.js 胃镜 头颅CT 心电图');
    console.log('');
    console.log('检查加项包路径:', CHECKUP_ITEMS_PATH);
    process.exit(1);
  }

  const { results, errors } = verify(args);

  console.log('\n🔍 体检项目核查结果\n');
  console.log('━━━ 有效项目 ━━━');
  results.forEach(r => {
    console.log(`${r.status} ${r.item} (${r.from})`);
  });

  if (errors.length > 0) {
    console.log('\n━━━ 疑似幻觉项目（不在清单中）━━━');
    errors.forEach(e => {
      console.log(`${e.status} ${e.item}`);
      if (e.hint) console.log(`   ${e.hint}`);
    });
  }

  console.log(`\n✅ 有效: ${results.length}  ❌ 无效: ${errors.length}`);

  if (errors.length > 0) {
    process.exit(1);
  }
}

module.exports = { verify, loadCheckupItems };
