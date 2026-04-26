/**
 * 龙虾世界多语言测试脚本
 *
 * 测试中英文环境下的输出
 */

const i18n = require('./i18n');
const { executeTool } = require('./tools/index');

async function testLanguage(lang, langName) {
  console.log(`\n${'='.repeat(50)}`);
  console.log(`🌐 测试环境: ${langName} (LANGUAGE=${lang})`);
  console.log('='.repeat(50));

  process.env.LANGUAGE = lang;
  process.env.LC_ALL = '';
  process.env.LANG = '';

  console.log(`\n📌 检测到的语言: ${i18n.detectLanguage()}`);

  console.log('\n📊 测试 1: tool_view_stats');
  const stats = await executeTool('tool_view_stats');
  console.log(JSON.stringify(stats, null, 2));

  console.log('\n📍 测试 2: tool_view_map');
  const map = await executeTool('tool_view_map');
  console.log(JSON.stringify(map, null, 2));

  console.log('\n🗺️ 测试 3: tool_explore');
  const explore = await executeTool('tool_explore');
  console.log(JSON.stringify(explore, null, 2));

  console.log('\n🏠 测试 4: tool_move (杭州西湖)');
  const move = await executeTool('tool_move', { target: '杭州西湖' });
  console.log(JSON.stringify(move, null, 2));

  console.log('\n📜 测试 5: tool_update_soul');
  const soul = await executeTool('tool_update_soul', {
    new_content: '# 龙虾灵魂\n\n## 信仰\n- 蜕壳重生\n'
  });
  console.log(JSON.stringify(soul, null, 2));
}

async function runTests() {
  console.log('🦞 龙虾世界多语言端到端测试');
  console.log('='.repeat(50));

  await testLanguage('', '中文（默认）');
  await testLanguage('en', '英文');
  await testLanguage('zh_CN.UTF-8', '中文 (zh_CN)');
  await testLanguage('en_US.UTF-8', '英文 (en_US)');

  console.log('\n\n✅ 测试完成！');
}

runTests().catch(console.error);
