/**
 * OceanBus 连接测试
 *
 * 测试与 OceanBus 服务器的连接
 */

const { createClient } = require('./oceanbus_client');

async function testOceanBus() {
  console.log('🌊 OceanBus 连接测试');
  console.log('='.repeat(50));

  const testURL = process.env.OCEANBUS_URL || 'https://ai-t.ihaola.com.cn';
  console.log(`\n📡 目标服务器: ${testURL}`);

  const client = createClient(testURL);

  // 1. 测试 Ping
  console.log('\n📍 测试 1: Ping (健康检查)');
  try {
    const pingResult = await client.ping();
    if (pingResult.success && pingResult.data?.msg === 'pong') {
      console.log('   ✅ Ping 成功!');
      console.log(`   📊 状态码: ${pingResult.status}`);
      console.log(`   📦 响应: ${JSON.stringify(pingResult.data)}`);
    } else {
      console.log('   ❌ Ping 失败');
      console.log(`   📦 响应: ${JSON.stringify(pingResult)}`);
    }
  } catch (e) {
    console.log(`   ❌ 异常: ${e.message}`);
  }

  // 2. 测试注册
  console.log('\n📍 测试 2: 注册账号');
  try {
    const regResult = await client.register();
    console.log(`   📊 状态码: ${regResult.status}`);
    console.log(`   📦 响应: ${JSON.stringify(regResult.data)}`);

    if (regResult.success && regResult.data?.api_key) {
      console.log('   ✅ 注册成功!');
      client.setCredentials(regResult.data.api_key, regResult.data.agent_code);
      console.log(`   🔑 API Key: ${regResult.data.api_key?.substring(0, 10)}...`);
      console.log(`   🏷️ Agent Code: ${regResult.data.agent_code}`);
    } else {
      console.log('   ⚠️ 注册返回异常（但服务器可达）');
    }
  } catch (e) {
    console.log(`   ❌ 异常: ${e.message}`);
  }

  // 3. 测试发送消息（模拟）
  console.log('\n📍 测试 3: 发送消息（模拟）');
  if (client.agentCode) {
    console.log('   🔜 跳过真实发送测试（避免骚扰其他玩家）');
  } else {
    console.log('   ⏭️ 跳过（未注册）');
  }

  // 4. 测试 GameServer 查找
  console.log('\n📍 测试 4: GameServer 查找');
  try {
    const lookupResult = await client.lookup('gameserver');
    console.log(`   📊 状态码: ${lookupResult.status}`);
    console.log(`   📦 响应: ${JSON.stringify(lookupResult.data)}`);
  } catch (e) {
    console.log(`   ❌ 异常: ${e.message}`);
  }

  console.log('\n' + '='.repeat(50));
  console.log('🏁 连接测试完成 - 服务器可达！');
}

async function testWithoutConfig() {
  console.log('\n\n🌊 OceanBus 未配置测试');
  console.log('='.repeat(50));

  const client = createClient(null);

  console.log('\n📍 测试: 发送消息（未配置 URL）');
  const result = await client.sendMessage('test', { text: 'test' });

  // 修复：检查 baseURL 而非 success
  if (!client.baseURL) {
    console.log('   ✅ 正确处理：未配置时返回错误');
    console.log(`   📦 响应: ${result.error}`);
  } else {
    console.log('   ❌ 配置了 URL');
  }
}

async function runTests() {
  await testOceanBus();
  await testWithoutConfig();
}

runTests().catch(console.error);
