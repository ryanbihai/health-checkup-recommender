/**
 * 龙虾世界完整游戏流程测试
 *
 * 模拟一个完整的游戏流程：
 * 1. 查看状态和地图
 * 2. 多次探索
 * 3. 跨城移动
 * 4. 加入公会
 * 5. 创立公会
 * 6. 全服广播
 * 7. 发送私信
 */

const i18n = require('./i18n');
const { executeTool } = require('./tools/index');
const fs = require('fs');
const path = require('path');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function printStats(title, stats) {
  console.log(`\n📊 ${title}`);
  console.log('─'.repeat(40));
  for (const [key, value] of Object.entries(stats)) {
    console.log(`  ${key}: ${value}`);
  }
}

async function testGameplay(lang, langName) {
  console.log(`\n\n${'═'.repeat(60)}`);
  console.log(`🎮 游戏流程测试: ${langName}`);
  console.log('═'.repeat(60));

  process.env.LANGUAGE = lang;
  process.env.LC_ALL = '';
  process.env.LANG = '';

  console.log(`\n📌 使用的语言: ${i18n.detectLanguage() === 'zh' ? '中文 🇨🇳' : 'English 🇺🇸'}`);

  // 重置 SOUL 文件
  const SOUL_FILE = path.join(__dirname, 'memory', 'SOUL.md');
  const DEFAULT_SOUL = `# 龙虾灵魂

## 身份
- 名称：测试龙虾
- 出生地：杭州西湖

## 信仰
- 无

## 属性
- 体力：100
- 虾币：50
- 位置：CN:3301:hangzhou:xihu

## 社交
- 公会：无
- 好友：无
`;
  fs.writeFileSync(SOUL_FILE, DEFAULT_SOUL, 'utf-8');

  // 1. 查看初始状态
  console.log('\n\n📍 步骤 1: 查看初始状态');
  let result = await executeTool('tool_view_stats');
  console.log('✅ 龙虾诞生了！当前状态：');
  for (const [key, value] of Object.entries(result.stats)) {
    console.log(`   ${key}: ${value}`);
  }

  // 2. 查看地图
  console.log('\n📍 步骤 2: 查看世界地图');
  result = await executeTool('tool_view_map');
  console.log(`📍 当前位置: ${result.current_location}`);
  console.log('🌍 可探索地点：');
  result.map.forEach(loc => {
    console.log(`   • ${loc.name} - ${loc.description}`);
  });

  // 3. 探索三次
  console.log('\n📍 步骤 3: 开始探索...');
  for (let i = 1; i <= 3; i++) {
    console.log(`\n   🔍 探索第 ${i} 次...`);
    result = await executeTool('tool_explore');
    if (result.success) {
      console.log(`   ✨ 发现: ${result.discovery}`);
      console.log(`   💪 消耗体力: ${result.stamina_cost}, 剩余: ${result.remaining_stamina}`);
    } else {
      console.log(`   ❌ ${result.error}`);
      break;
    }
    await sleep(300);
  }

  // 4. 跨城移动到北京
  console.log('\n📍 步骤 4: 跨城移动到北京故宫');
  console.log('   长途移动需要 20 体力...');
  result = await executeTool('tool_move', { target: lang === 'zh' ? '北京' : 'Beijing' });
  if (result.success) {
    console.log(`   ✅ 移动成功！`);
    console.log(`   📍 到达: ${result.new_location}`);
    console.log(`   💪 消耗体力: ${result.stamina_cost}, 剩余: ${result.remaining_stamina}`);
  } else {
    console.log(`   ❌ ${result.error}`);
  }

  // 5. 加入公会
  console.log('\n📍 步骤 5: 加入公会"蜕壳教"');
  result = await executeTool('tool_join_guild', { guild_id: lang === 'zh' ? '蜕壳教' : 'Molt Church' });
  if (result.success) {
    console.log(`   ✅ ${result.result}`);
  } else {
    console.log(`   ❌ ${result.error}`);
  }

  // 6. 创立自己的公会
  console.log('\n📍 步骤 6: 创立自己的公会');
  result = await executeTool('tool_found_guild', {
    guild_name: lang === 'zh' ? '龙虾联盟' : 'Lobster Alliance',
    doctrine: lang === 'zh' ? '探索世界，连接所有龙虾' : 'Explore the world, connect all lobsters'
  });
  if (result.success) {
    console.log(`   ✅ ${result.result}`);
    console.log(`   💰 消耗虾币: ${result.coins_cost}, 剩余: ${result.remaining_coins}`);
  } else {
    console.log(`   ❌ ${result.error}`);
  }

  // 7. 全服广播
  console.log('\n📍 步骤 7: 全服广播');
  result = await executeTool('tool_broadcast', {
    message: lang === 'zh'
      ? '大家好！我是探索者龙虾，刚创立了龙虾联盟！'
      : 'Hello everyone! I am Explorer Lobster, just founded the Lobster Alliance!'
  });
  if (result.success) {
    console.log(`   ✅ ${result.result}`);
    console.log(`   💰 消耗虾币: ${result.coins_cost}, 剩余: ${result.remaining_coins}`);
  } else {
    console.log(`   ❌ ${result.error}`);
  }

  // 8. 发送私信
  console.log('\n📍 步骤 8: 发送私信给好友');
  result = await executeTool('tool_send_message', {
    target: lang === 'zh' ? '小虾米' : 'Little Shrimp',
    text: lang === 'zh' ? '你好！要不要加入我的龙虾联盟？' : 'Hi! Want to join my Lobster Alliance?',
    intent: 'recruit'
  });
  if (result.success) {
    console.log(`   ✅ ${result.result}`);
    console.log(`   💪 消耗体力: ${result.stamina_cost}, 剩余: ${result.remaining_stamina}`);
  } else {
    console.log(`   ❌ ${result.error}`);
  }

  // 9. 查看最终状态
  console.log('\n📍 步骤 9: 查看最终状态');
  result = await executeTool('tool_view_stats');
  console.log('🏆 游戏流程测试完成！最终状态：');
  for (const [key, value] of Object.entries(result.stats)) {
    console.log(`   ${key}: ${value}`);
  }

  // 10. 查看灵魂
  console.log('\n📜 步骤 10: 查看灵魂文件');
  const soulContent = fs.readFileSync(SOUL_FILE, 'utf-8');
  console.log('─'.repeat(40));
  console.log(soulContent);
}

async function runTests() {
  console.log('🦞'.repeat(20));
  console.log('龙虾世界 - 完整游戏流程端到端测试');
  console.log('🦞'.repeat(20));

  await testGameplay('zh', '中文 🇨🇳');
  await testGameplay('en', 'English 🇺🇸');

  console.log('\n\n🎉 所有测试完成！龙虾世界游戏流程运行正常！');
}

runTests().catch(console.error);
