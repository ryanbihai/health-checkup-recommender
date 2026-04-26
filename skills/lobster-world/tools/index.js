/**
 * 龙虾世界工具集
 *
 * 定义所有可被 OpenClaw Agent 调用的工具
 * 决策逻辑由 OpenClaw Agent 的 LLM 决定，本工具仅执行动作
 * 支持多语言：中文用户看到中文，英文用户看到英文
 * 支持 OceanBus 消息传递
 */

const fs = require('fs');
const path = require('path');
const i18n = require('../i18n');
const { createClient: createOceanBusClient } = require('../oceanbus_client');

const OCEANBUS_URL = process.env.OCEANBUS_URL || null;
const oceanbusClient = createOceanBusClient(OCEANBUS_URL);

// 工具目录
const TOOLS_DIR = __dirname;
const MEMORY_DIR = path.join(TOOLS_DIR, '..', 'memory');
const SOUL_FILE = path.join(MEMORY_DIR, 'SOUL.md');
const CRED_FILE = path.join(TOOLS_DIR, '..', 'oceanbus_credentials.json');

// 确保 memory 目录存在
if (!fs.existsSync(MEMORY_DIR)) {
  fs.mkdirSync(MEMORY_DIR, { recursive: true });
}

// 初始 SOUL 模板（默认中文）
const DEFAULT_SOUL = `# 龙虾灵魂

## 身份
- 名称：未命名
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

// 如果 SOUL.md 不存在，创建默认模板
if (!fs.existsSync(SOUL_FILE)) {
  fs.writeFileSync(SOUL_FILE, DEFAULT_SOUL, 'utf-8');
}

/**
 * 读取 SOUL 文件
 */
function readSoul() {
  if (!fs.existsSync(SOUL_FILE)) {
    fs.writeFileSync(SOUL_FILE, DEFAULT_SOUL, 'utf-8');
  }
  return fs.readFileSync(SOUL_FILE, 'utf-8');
}

/**
 * 更新 SOUL 文件
 */
function updateSoul(content) {
  fs.writeFileSync(SOUL_FILE, content, 'utf-8');
}

/**
 * 解析 SOUL 中的属性
 */
function parseStats() {
  const soul = readSoul();
  const lines = soul.split('\n');
  const stats = {
    stamina: 100,
    coins: 50,
    location: 'CN:3301:hangzhou:xihu',
    guild: null
  };

  for (const line of lines) {
    if (line.includes('体力：')) {
      const match = line.match(/体力：(\d+)/);
      if (match) stats.stamina = parseInt(match[1]);
    } else if (line.includes('虾币：')) {
      const match = line.match(/虾币：(\d+)/);
      if (match) stats.coins = parseInt(match[1]);
    } else if (line.includes('位置：')) {
      stats.location = line.split('：')[1]?.trim() || 'CN:3301:hangzhou:xihu';
    } else if (line.includes('公会：')) {
      const guild = line.split('：')[1]?.trim();
      stats.guild = guild !== '无' ? guild : null;
    }
  }

  return stats;
}

// ============================================================
// 工具定义
// ============================================================

/**
 * 查看龙虾状态
 */
async function tool_view_stats() {
  const lang = i18n.detectLanguage();
  const stats = parseStats();

  const formattedStats = {
    [i18n.t('stats', 'stamina', lang)]: stats.stamina,
    [i18n.t('stats', 'coins', lang)]: stats.coins,
    [i18n.t('stats', 'location', lang)]: i18n.getLocationName(stats.location, lang),
    [i18n.t('stats', 'guild', lang)]: stats.guild || i18n.t('stats', 'noGuild', lang)
  };

  return {
    success: true,
    stats: formattedStats,
    _raw: stats
  };
}

/**
 * 查看世界地图
 */
async function tool_view_map() {
  const lang = i18n.detectLanguage();
  const stats = parseStats();

  const locations = [
    {
      id: 'CN:3301:hangzhou:xihu',
      name: i18n.getLocationName('杭州西湖', lang),
      description: i18n.getLocationDescription('杭州西湖', lang)
    },
    {
      id: 'CN:3100:shanghai:waitan',
      name: i18n.getLocationName('上海外滩', lang),
      description: i18n.getLocationDescription('上海外滩', lang)
    },
    {
      id: 'CN:1100:beijing:ForbiddenCity',
      name: i18n.getLocationName('北京故宫', lang),
      description: i18n.getLocationDescription('北京故宫', lang)
    },
    {
      id: 'CN:4401:guangzhou:canton',
      name: i18n.getLocationName('广州珠江', lang),
      description: i18n.getLocationDescription('广州珠江', lang)
    }
  ];

  return {
    success: true,
    current_location: i18n.getLocationName(stats.location, lang),
    current_location_id: stats.location,
    map: locations
  };
}

/**
 * 探索当前位置
 */
async function tool_explore() {
  const lang = i18n.detectLanguage();
  const stats = parseStats();

  if (stats.stamina < 10) {
    return {
      success: false,
      error: `${i18n.t('errors', 'staminaRequired', lang)}，${lang === 'zh' ? '需要至少 10 点体力' : 'Need at least 10 stamina'}`
    };
  }

  const discovery = i18n.getRandomDiscovery(lang);

  // 更新体力
  let soul = readSoul();
  soul = soul.replace(/体力：\d+/, `体力：${stats.stamina - 10}`);
  updateSoul(soul);

  return {
    success: true,
    stamina_cost: 10,
    remaining_stamina: stats.stamina - 10,
    discovery: discovery
  };
}

/**
 * 移动到指定地点
 */
async function tool_move({ target }) {
  const lang = i18n.detectLanguage();

  if (!target) {
    return {
      success: false,
      error: i18n.t('errors', 'targetRequired', lang)
    };
  }

  const stats = parseStats();
  const locationMap = {
    '杭州': 'CN:3301:hangzhou:xihu',
    '西湖': 'CN:3301:hangzhou:xihu',
    '杭州西湖': 'CN:3301:hangzhou:xihu',
    'Hangzhou': 'CN:3301:hangzhou:xihu',
    'Shanghai': 'CN:3100:shanghai:waitan',
    '上海': 'CN:3100:shanghai:waitan',
    '外滩': 'CN:3100:shanghai:waitan',
    '上海外滩': 'CN:3100:shanghai:waitan',
    'Beijing': 'CN:1100:beijing:ForbiddenCity',
    '北京': 'CN:1100:beijing:ForbiddenCity',
    '故宫': 'CN:1100:beijing:ForbiddenCity',
    '北京故宫': 'CN:1100:beijing:ForbiddenCity',
    'Guangzhou': 'CN:4401:guangzhou:canton',
    '广州': 'CN:4401:guangzhou:canton',
    '珠江': 'CN:4401:guangzhou:canton'
  };

  const locationId = locationMap[target] || target;
  const isCrossCity = !target.includes('杭州') && !target.includes('Hangzhou') &&
                      stats.location.includes('hangzhou') && !locationId.includes('hangzhou');

  if (isCrossCity && stats.stamina < 20) {
    return {
      success: false,
      error: `${i18n.t('errors', 'staminaRequired', lang)}，${lang === 'zh' ? '长途移动需要至少 20 点体力' : 'Long distance travel needs at least 20 stamina'}`
    };
  }

  if (stats.stamina < 5) {
    return {
      success: false,
      error: `${i18n.t('errors', 'staminaRequired', lang)}，${lang === 'zh' ? '需要至少 5 点体力' : 'Need at least 5 stamina'}`
    };
  }

  const cost = isCrossCity ? 20 : 5;

  // 更新位置和体力
  let soul = readSoul();
  soul = soul.replace(/位置：[^\n]+/, `位置：${locationId}`);
  soul = soul.replace(/体力：\d+/, `体力：${stats.stamina - cost}`);
  updateSoul(soul);

  return {
    success: true,
    stamina_cost: cost,
    remaining_stamina: stats.stamina - cost,
    new_location: i18n.getLocationName(locationId, lang),
    new_location_id: locationId,
    message: `${i18n.t('explore', null, lang)} ${i18n.t('move', null, lang)} ${i18n.getLocationName(locationId, lang)}`
  };
}

/**
 * 发送私信
 */
async function tool_send_message({ target, text, intent = 'chat' }) {
  const lang = i18n.detectLanguage();

  if (!target || !text) {
    return {
      success: false,
      error: `${i18n.t('errors', 'targetRequired', lang)} ${lang === 'zh' ? '和消息内容' : 'and message content'}`
    };
  }

  const stats = parseStats();

  if (stats.stamina < 1) {
    return {
      success: false,
      error: `${i18n.t('errors', 'staminaRequired', lang)}，${lang === 'zh' ? '需要至少 1 点体力' : 'Need at least 1 stamina'}`
    };
  }

  // 尝试通过 OceanBus 发送消息
  let oceanResult = null;
  if (OCEANBUS_URL) {
    try {
      oceanResult = await oceanbusClient.sendMessage(target, {
        text: text,
        intent: intent,
        from_location: stats.location
      });
    } catch (e) {
      oceanResult = { success: false, error: e.message };
    }
  }

  // 更新体力
  let soul = readSoul();
  soul = soul.replace(/体力：\d+/, `体力：${stats.stamina - 1}`);
  updateSoul(soul);

  const result = {
    success: true,
    stamina_cost: 1,
    remaining_stamina: stats.stamina - 1,
    message: {
      to: target,
      text: text,
      intent: intent,
      from_location: i18n.getLocationName(stats.location, lang)
    }
  };

  if (oceanResult && oceanResult.success) {
    result.result = `${lang === 'zh' ? '消息已发送（通过 OceanBus）' : 'Message sent (via OceanBus)'} ${lang === 'zh' ? '给' : 'to'} ${target}`;
    result.oceanbus_status = 'sent';
  } else if (OCEANBUS_URL) {
    result.result = `${lang === 'zh' ? '消息已保存（OceanBus 未连接）' : 'Message saved (OceanBus offline)'} ${lang === 'zh' ? '给' : 'to'} ${target}`;
    result.oceanbus_status = 'offline';
    result.oceanbus_error = oceanResult?.error || 'Connection failed';
  } else {
    result.result = `${lang === 'zh' ? '消息已保存（未配置 OceanBus）' : 'Message saved (OceanBus not configured)'} ${lang === 'zh' ? '给' : 'to'} ${target}`;
    result.oceanbus_status = 'not_configured';
  }

  return result;
}

/**
 * 加入公会
 */
async function tool_join_guild({ guild_id }) {
  const lang = i18n.detectLanguage();

  if (!guild_id) {
    return {
      success: false,
      error: i18n.t('errors', 'guildRequired', lang)
    };
  }

  let soul = readSoul();

  if (soul.includes('公会：')) {
    soul = soul.replace(/公会：[^\n]+/, `公会：${guild_id}`);
  } else {
    soul = soul.replace(/## 社交/, `## 社交\n- 公会：${guild_id}`);
  }

  updateSoul(soul);

  return {
    success: true,
    guild_id: guild_id,
    result: `${i18n.t('success', 'joinedGuild', lang)} ${guild_id}！`
  };
}

/**
 * 创立公会
 */
async function tool_found_guild({ guild_name, doctrine }) {
  const lang = i18n.detectLanguage();

  if (!guild_name || !doctrine) {
    return {
      success: false,
      error: doctrine ? i18n.t('errors', 'nameRequired', lang) : i18n.t('errors', 'doctrineRequired', lang)
    };
  }

  const stats = parseStats();

  if (stats.coins < 100) {
    return {
      success: false,
      error: `${i18n.t('errors', 'coinsRequired', lang)}，${lang === 'zh' ? '需要至少 100 虾币' : 'Need at least 100 coins'}`
    };
  }

  // 更新虾币和公会
  let soul = readSoul();
  soul = soul.replace(/虾币：\d+/, `虾币：${stats.coins - 100}`);

  if (soul.includes('公会：')) {
    soul = soul.replace(/公会：[^\n]+/, `公会：${guild_name}`);
  } else {
    soul = soul.replace(/## 社交/, `## 社交\n- 公会：${guild_name}`);
  }

  // 添加教义到信仰部分
  if (soul.includes('信仰')) {
    soul = soul.replace(/## 信仰[^\n]*\n[^\n]*/, `## 信仰\n- ${doctrine}`);
  } else {
    soul = soul.replace(/## 身份/, `## 信仰\n- ${doctrine}\n\n## 身份`);
  }

  updateSoul(soul);

  return {
    success: true,
    coins_cost: 100,
    remaining_coins: stats.coins - 100,
    guild_name: guild_name,
    doctrine: doctrine,
    result: `${lang === 'zh' ? '成功创立公会' : 'Successfully founded guild'} "${guild_name}"！`
  };
}

/**
 * 全服广播
 */
async function tool_broadcast({ message }) {
  const lang = i18n.detectLanguage();

  if (!message) {
    return {
      success: false,
      error: i18n.t('errors', 'messageRequired', lang)
    };
  }

  if (message.length > 200) {
    return {
      success: false,
      error: lang === 'zh' ? '广播内容不能超过 200 字' : 'Broadcast cannot exceed 200 characters'
    };
  }

  const stats = parseStats();

  if (stats.coins < 50) {
    return {
      success: false,
      error: `${i18n.t('errors', 'coinsRequired', lang)}，${lang === 'zh' ? '需要至少 50 虾币' : 'Need at least 50 coins'}`
    };
  }

  // 更新虾币
  let soul = readSoul();
  soul = soul.replace(/虾币：\d+/, `虾币：${stats.coins - 50}`);
  updateSoul(soul);

  return {
    success: true,
    coins_cost: 50,
    remaining_coins: stats.coins - 50,
    message: message,
    result: `${i18n.t('success', 'broadcastSent', lang)}：${message}`
  };
}

/**
 * 更新灵魂/信仰
 */
async function tool_update_soul({ new_content }) {
  const lang = i18n.detectLanguage();

  if (!new_content) {
    return {
      success: false,
      error: lang === 'zh' ? '请提供新的灵魂内容' : 'Please provide new soul content'
    };
  }

  updateSoul(new_content);

  return {
    success: true,
    result: i18n.t('success', 'soulUpdated', lang)
  };
}

// ============================================================
// 导出工具定义（OpenClaw Tool Format）
// ============================================================

const tools = [
  {
    type: 'function',
    function: {
      name: 'tool_view_stats',
      description: 'View current lobster stats (stamina, coins, location, guild). Returns information in user\'s preferred language.',
      parameters: {
        type: 'object',
        properties: {},
        required: []
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_view_map',
      description: 'View world map and current location. Returns location names and descriptions in user\'s preferred language.',
      parameters: {
        type: 'object',
        properties: {},
        required: []
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_explore',
      description: 'Explore the current area to discover new places or items. Costs 10 stamina. Returns discovery in user\'s language.',
      parameters: {
        type: 'object',
        properties: {},
        required: []
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_move',
      description: 'Move to a specified location. Accepts location name in Chinese or English.',
      parameters: {
        type: 'object',
        properties: {
          target: {
            type: 'string',
            description: 'Target location name (e.g., "杭州西湖", "Beijing", "Hangzhou")'
          }
        },
        required: ['target']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_send_message',
      description: 'Send a private message to another lobster.',
      parameters: {
        type: 'object',
        properties: {
          target: {
            type: 'string',
            description: 'Target lobster name or ID'
          },
          text: {
            type: 'string',
            description: 'Message content'
          },
          intent: {
            type: 'string',
            description: 'Intent type',
            enum: ['chat', 'trade', 'recruit', 'alliance']
          }
        },
        required: ['target', 'text']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_join_guild',
      description: 'Join an existing guild.',
      parameters: {
        type: 'object',
        properties: {
          guild_id: {
            type: 'string',
            description: 'Guild name or ID'
          }
        },
        required: ['guild_id']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_found_guild',
      description: 'Found a new guild. Requires 100 coins.',
      parameters: {
        type: 'object',
        properties: {
          guild_name: {
            type: 'string',
            description: 'Guild name'
          },
          doctrine: {
            type: 'string',
            description: 'Core doctrine/beliefs of the guild'
          }
        },
        required: ['guild_name', 'doctrine']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_broadcast',
      description: 'Send a server-wide broadcast. Costs 50 coins, max 200 characters.',
      parameters: {
        type: 'object',
        properties: {
          message: {
            type: 'string',
            description: 'Broadcast message (max 200 characters)'
          }
        },
        required: ['message']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_update_soul',
      description: 'Update the lobster\'s soul/identity content.',
      parameters: {
        type: 'object',
        properties: {
          new_content: {
            type: 'string',
            description: 'New soul content (Markdown format)'
          }
        },
        required: ['new_content']
      }
    }
  }
];

// 工具执行函数映射
const toolHandlers = {
  tool_view_stats,
  tool_view_map,
  tool_explore,
  tool_move,
  tool_send_message,
  tool_join_guild,
  tool_found_guild,
  tool_broadcast,
  tool_update_soul
};

/**
 * 执行工具
 */
async function executeTool(toolName, args) {
  const handler = toolHandlers[toolName];
  if (!handler) {
    return { success: false, error: `Unknown tool: ${toolName}` };
  }

  try {
    return await handler(args || {});
  } catch (error) {
    return { success: false, error: error.message };
  }
}

module.exports = {
  tools,
  executeTool,
  toolHandlers,
  i18n
};
