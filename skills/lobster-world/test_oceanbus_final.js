/**
 * OceanBus API 完整测试
 */

const { createClient } = require('./oceanbus_client');

async function test() {
  console.log('🌊 OceanBus API 完整测试');
  console.log('='.repeat(60));

  const client = createClient();

  // 1. Ping
  console.log('\n📍 1. Ping 健康检查');
  const ping = await client.ping();
  console.log(`   ${ping.success ? '✅' : '❌'} ${ping.status}: ${JSON.stringify(ping.data)}`);

  // 2. 注册两只龙虾
  console.log('\n📍 2. 注册龙虾 A');
  const lobsterA = await client.register('lobster_A');
  console.log(`   ${lobsterA.success ? '✅' : '❌'} ${lobsterA.status}`);
  console.log(`   agent_code: ${lobsterA.data?.data?.agent_code}`);

  const { api_key: keyA, agent_code: codeA } = lobsterA.data?.data || {};
  client.setCredentials(keyA, codeA);

  console.log('\n📍 3. 注册龙虾 B');
  const clientB = createClient();
  const lobsterB = await clientB.register('lobster_B');
  console.log(`   ${lobsterB.success ? '✅' : '❌'} ${lobsterB.status}`);
  const { agent_code: codeB } = lobsterB.data?.data || {};
  console.log(`   agent_code: ${codeB}`);

  // 4. A 查找 B 的 openid
  console.log('\n📍 4. 龙虾 A 查找龙虾 B 的 OpenID');
  const lookupB = await client.lookup(codeB);
  console.log(`   ${lookupB.success ? '✅' : '❌'} ${lookupB.status}`);
  const toOpenid = lookupB.data?.data?.to_openid;
  console.log(`   to_openid: ${toOpenid?.substring(0, 30)}...`);

  // 5. A 发送消息给 B
  if (toOpenid) {
    console.log('\n📍 5. 龙虾 A 发送消息给龙虾 B');
    const send = await client.sendMessage(toOpenid, '你好，B！我是 A！', 'msg_' + Date.now());
    console.log(`   ${send.success ? '✅' : '⚠️'} ${send.status}: ${JSON.stringify(send.data)}`);
  }

  // 6. A 同步信箱
  console.log('\n📍 6. 龙虾 A 同步信箱');
  const syncA = await client.syncMessages(0, 10);
  console.log(`   ${syncA.success ? '✅' : '❌'} ${syncA.status}`);
  const messages = syncA.data?.data?.messages || [];
  console.log(`   收到消息数: ${messages.length}`);
  messages.forEach((msg, i) => {
    console.log(`   [${i + 1}] from: ${msg.from_openid?.substring(0, 20)}...`);
    console.log(`       content: ${msg.content}`);
  });

  // 7. B 同步信箱
  console.log('\n📍 7. 龙虾 B 同步信箱');
  const clientB2 = createClient();
  clientB2.setCredentials(lobsterB.data?.data?.api_key, codeB);
  const syncB = await clientB2.syncMessages(0, 10);
  console.log(`   ${syncB.success ? '✅' : '❌'} ${syncB.status}`);
  const messagesB = syncB.data?.data?.messages || [];
  console.log(`   收到消息数: ${messagesB.length}`);
  messagesB.forEach((msg, i) => {
    console.log(`   [${i + 1}] from: ${msg.from_openid?.substring(0, 20)}...`);
    console.log(`       content: ${msg.content}`);
  });

  console.log('\n' + '='.repeat(60));
  console.log('🏁 OceanBus 完整测试完成！');
  console.log('\n📋 测试的 API 端点:');
  console.log('   POST /api/l0/agents/register - 注册新 Agent');
  console.log('   GET  /api/l0/agents/lookup - 精确寻址');
  console.log('   POST /api/l0/messages - 发送消息');
  console.log('   GET  /api/l0/messages/sync - 同步信箱');
}

test().catch(console.error);
