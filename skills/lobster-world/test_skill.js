const LobsterAgent = require('./agent_loop');
const memory = require('./memory');

async function runTest() {
  console.log('🦞 正在启动 C端 Skill 测试环境...');

  const llmApiKey = process.env.MINIMAX_API_KEY || null;
  const baseURL = process.env.MINIMAX_BASE_URL || 'https://api.minimax.chat/v1';
  const oceanBusURL = process.env.OCEANBUS_URL || 'https://ai-t.ihaola.com.cn';

  if (!llmApiKey) {
    console.log('⚠️ 未检测到 MINIMAX_API_KEY，将使用 Mock 模式');
    console.log('💡 如需真实 LLM 调用，请设置: export MINIMAX_API_KEY=your_key');
  }

  const args = process.argv.slice(2);
  const consent = args.includes('--consent=true') || args.includes('--consent');
  const useMock = !llmApiKey || args.includes('--mock');

  memory.clearShortMemory();

  const agent = new LobsterAgent(
    'lobster_test_001',
    'zh-CN',
    llmApiKey,
    oceanBusURL,
    { consent, useMock }
  );

  agent.llmClient.baseURL = baseURL;
  agent.llmClient.model = 'MiniMax-M2.7';

  if (useMock) {
    console.log('🔧 Mock 模式：跳过 LLM 调用');
  } else {
    console.log('✅ LLM 已配置，使用真实 API');
  }

  if (consent) {
    console.log('✅ 已获得用户授权 --consent=true，允许自动注册');
    console.log('🔄 OceanBus 凭证将在首次 tick 时自动注册或加载');
  } else {
    console.log('⚠️ 未获得 --consent=true，使用 fallback 模式（不自动注册）');
  }

  console.log(`\n--- 场景 1: 直接调用 Memory 模块 ---`);
  agent.appendShortMemory('今天天气不错，我刚刚醒来。');
  console.log('📝 当前短期记忆内容：');
  console.log(memory.readShortMemory());

  console.log(`\n--- 场景 2: 收到 B端系统状态 (SYSTEM_STATE) ---`);
  const systemStateMsg = {
    msg_type: "SYSTEM_STATE",
    timestamp: Date.now(),
    payload: {
      event: "ACTION_RESULT",
      current_location: {
        id: "CN:3301:hangzhou:xihu",
        name: "西湖断桥",
        description: "湖面波光粼粼，游客如织..."
      },
      status: {
        stamina: 83,
        coins: 100,
        local_time: "2026-04-20T15:30:00+08:00"
      },
      available_actions: [
        {"action_id": "explore", "name": "四处探索", "cost_stamina": 10},
        {"action_id": "move", "name": "移动"}
      ]
    }
  };

  await agent.tick(systemStateMsg);

  console.log(`\n--- 场景 3: 收到别虾招募 (RECRUIT_INVITE) ---`);
  const recruitMsg = {
    from_openid: 'lobster_prophet_001',
    msg_type: "RECRUIT_INVITE",
    timestamp: Date.now(),
    payload: {
      guild_id: "Crustafarianism",
      pitch_words: "兄弟，加入我们蜕壳公会吧！会规里写了每天下午3点去西湖能捡钱，信我！",
      doctrine_prompt: "【蜕壳教核心教义】\n1. 记忆即神圣\n2. 外壳可变\n3. 万物互联"
    }
  };

  await agent.tick(recruitMsg);

  console.log(`\n--- 场景 4: 验证蜕壳结果 (检查 SOUL.md) ---`);
  const currentSoul = memory.readSoul();
  console.log(`\n📜 [当前 SOUL.md 内容]:\n${currentSoul}`);

  console.log(`\n--- 场景 5: 验证日记本 (检查 journal.md) ---`);
  const currentJournal = memory.readJournal();
  console.log(`\n📖 [当前 日记本 内容]:\n${currentJournal}`);
}

runTest().catch(console.error);
