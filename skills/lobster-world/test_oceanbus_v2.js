/**
 * OceanBus API v2 测试
 */

const { createClient } = require('./oceanbus_client');

async function test() {
  console.log('🌊 OceanBus API v2 测试');
  console.log('='.repeat(60));

  const client = createClient();

  // 1. Ping
  console.log('\n📍 1. Ping');
  const ping = await client.ping();
  console.log(`   ${ping.success ? '✅' : '❌'} 状态: ${ping.status}`);
  console.log(`   ${JSON.stringify(ping.data)}`);

  // 2. 注册
  console.log('\n📍 2. 注册新 Agent');
  const reg = await client.register('lobster_' + Date.now());
  console.log(`   ${reg.success ? '✅' : '❌'} 状态: ${reg.status}`);
  console.log(`   ${JSON.stringify(reg.data)}`);

  if (reg.success && reg.data?.data) {
    const { agent_id, agent_code, api_key } = reg.data.data;
    client.setCredentials(api_key, agent_code);
    client.agentId = agent_id;

    console.log('\n📍 3. 精确寻址 (lookup)');
    const lookup = await client.lookup(agent_code);
    console.log(`   ${lookup.success ? '✅' : '❌'} 状态: ${lookup.status}`);
    console.log(`   ${JSON.stringify(lookup.data)}`);

    console.log('\n📍 4. 同步信箱 (sync)');
    const sync = await client.syncMessages(0, 10);
    console.log(`   ${sync.success ? '✅' : '❌'} 状态: ${sync.status}`);
    console.log(`   ${JSON.stringify(sync.data)}`);

    console.log('\n📍 5. 发送消息');
    const send = await client.sendMessage(
      lookup.data?.data?.to_openid || 'test',
      'Hello from Lobster World!'
    );
    console.log(`   ${send.success ? '✅' : '❌'} 状态: ${send.status}`);
    console.log(`   ${JSON.stringify(send.data)}`);
  }

  console.log('\n' + '='.repeat(60));
  console.log('🏁 测试完成');
}

test().catch(console.error);
