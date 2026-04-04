/**
 * check_conflicts.js - 体检项目冲突检测脚本
 * 父子项去重：选择父项时自动移除其子项
 *
 * 冲突链：
 *   Item030(常规检查2) > Item029(常规检查1)
 *   Item154(胃功能全项) > Item016(胃功能3项), Item155(胃泌素-17)
 *   Item107(甲功5项A) > Item105(甲功3项A)
 *   Item108(甲功5项B) > Item106(甲功3项B)
 *   Item111(甲功7项) > Item105,106,107,108,109
 *   Item020(心肌酶5项) > Item160,161,157,158,159
 *   Item161(心肌酶4项) > Item157,158,159
 *   Item084(肝功能15项) > Item083,082,081,080,079,078,071,074...
 *   Item083(肝功能11项) > Item082,081,080,079,078,071,074...
 *   Item082(肝功能9项) > Item080,079,078,071,074,076,077
 *   Item081(肝功能7项B) > Item080,079,078,071,074,072,073
 *   Item080(肝功能7项) > Item079,078,071,074,072,073
 *   Item079(肝功能6项) > Item071,074,076
 *   Item078(肝功能4项) > Item071,074
 *   Item175(血脂9项) > Item174,172,171,173,176,177,178
 *   Item174(血脂7项) > Item172,173,176,177,178
 *   Item172(血脂5项) > Item173,176,177
 *   Item173(血脂4项) > Item176,177
 *   Item193(TM7男) > Item191(TM5男)
 *   Item194(TM7女) > Item192(TM5女)
 *   Item181(视力+眼底镜) > Item183(眼底镜)
 *   Item182(视力+眼底+裂隙灯) > Item183(眼底镜)
 */

const fs = require('fs');
const path = require('path');

const ITEMS_JSON_PATH = path.join(__dirname, '..', 'reference', 'checkup_items.json');
let ITEMS_DB = {};
try {
  ITEMS_DB = JSON.parse(fs.readFileSync(ITEMS_JSON_PATH, 'utf-8')).items || {};
} catch(e) {
  console.error('[ERROR] Cannot load items:', e.message);
  process.exit(1);
}

const CONFLICT_MAP = {
  'Item030': ['Item029'],
  'Item154': ['Item016', 'Item155'],
  'Item107': ['Item105'],
  'Item108': ['Item106'],
  'Item111': ['Item105', 'Item106', 'Item107', 'Item108', 'Item109'],
  'Item020': ['Item160', 'Item161', 'Item157', 'Item158', 'Item159'],
  'Item161': ['Item157', 'Item158', 'Item159'],
  'Item084': ['Item083', 'Item082', 'Item081', 'Item080', 'Item079', 'Item078', 'Item071', 'Item074', 'Item072', 'Item073', 'Item075'],
  'Item083': ['Item082', 'Item081', 'Item080', 'Item079', 'Item078', 'Item071', 'Item074', 'Item072', 'Item073', 'Item075'],
  'Item082': ['Item080', 'Item079', 'Item078', 'Item071', 'Item074', 'Item076', 'Item077'],
  'Item081': ['Item080', 'Item079', 'Item078', 'Item071', 'Item074', 'Item072', 'Item073'],
  'Item080': ['Item079', 'Item078', 'Item071', 'Item074', 'Item072', 'Item073'],
  'Item079': ['Item071', 'Item074', 'Item076'],
  'Item078': ['Item071', 'Item074'],
  'Item175': ['Item174', 'Item172', 'Item171', 'Item173', 'Item176', 'Item177', 'Item178'],
  'Item174': ['Item172', 'Item173', 'Item176', 'Item177', 'Item178'],
  'Item172': ['Item173', 'Item176', 'Item177'],
  'Item173': ['Item176', 'Item177'],
  'Item193': ['Item191'],
  'Item194': ['Item192'],
  'Item181': ['Item183'],
  'Item182': ['Item183'],
};

/**
 * 检测并解决冲突
 * 策略：若父项和子项同时存在，保留父项，删除子项
 *
 * @param {string[]} itemIds - 输入的 ItemID 数组
 * @returns {{ resolved: string[], removed: {id,name,reason,supersededBy}[] }}
 */
function checkConflicts(itemIds) {
  const unique = [...new Set(itemIds.map(id => id.toLowerCase()))];
  const toRemove = new Set();
  const removed = [];

  for (const id of unique) {
    if (toRemove.has(id)) continue;
    const subsets = CONFLICT_MAP[id.charAt(0).toUpperCase() + id.slice(1)];
    if (!subsets) continue;

    for (const subId of subsets) {
      const subIdLower = subId.toLowerCase();
      if (unique.includes(subIdLower) && !toRemove.has(subIdLower)) {
        toRemove.add(subIdLower);
        removed.push({
          id: subIdLower,
          name: ITEMS_DB[subId]?.name || subId,
          reason: `已被 ${id} ${ITEMS_DB[id.charAt(0).toUpperCase() + id.slice(1)]?.name || id} 包含`,
          supersededBy: id,
        });
      }
    }
  }

  const resolved = unique.filter(id => !toRemove.has(id));
  const total = resolved.reduce((s, id) => s + (ITEMS_DB[id]?.price || 0), 0);

  return { resolved, removed, total };
}

// CLI
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('用法: node check_conflicts.js Item029 Item030 Item154 Item016 Item155');
    console.log('');
    const demo = ['Item029', 'Item030', 'Item154', 'Item016', 'Item155', 'Item083', 'Item071', 'Item107', 'Item105'];
    console.log('演示:', demo.join(', '));
    const r = checkConflicts(demo);
    if (r.removed.length) {
      r.removed.forEach(x => console.log(`  ❌ ${x.id} ${x.name} → ${x.reason}`));
    }
    console.log(`\n✅ 去重后: ${r.resolved.join(', ')}  共${r.resolved.length}项 ¥${r.total}`);
    process.exit(r.removed.length > 0 ? 1 : 0);
    return;
  }

  const r = checkConflicts(args);
  if (r.removed.length) {
    r.removed.forEach(x => console.log(`❌ ${x.id} ${x.name} → ${x.reason}`));
    console.log(`\n去重后: ${r.resolved.join(', ')}  共${r.resolved.length}项 ¥${r.total}`);
    process.exit(1);
  }
  console.log(`✅ 无冲突  共${r.resolved.length}项 ¥${r.total}`);
  process.exit(0);
}

module.exports = { checkConflicts, CONFLICT_MAP };
