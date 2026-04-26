/**
 * 龙虾世界工具集
 *
 * 定义所有可被 OpenClaw Agent 调用的工具
 * 决策逻辑由 OpenClaw Agent 决定，本工具仅执行本地动作
 */

const fs = require('fs');
const path = require('path');

// 工具目录
const TOOLS_DIR = __dirname;
const MEMORY_DIR = path.join(TOOLS_DIR, '..', 'memory');
const SOUL_FILE = path.join(MEMORY_DIR, 'SOUL.md');

// 确保 memory 目录存在
if (!fs.existsSync(MEMORY_DIR)) {
  fs.mkdirSync(MEMORY_DIR, { recursive: true });
}

// 初始 SOUL 模板
const DEFAULT_SOUL = `# 龙虾灵魂

## 身份
- 名称：未命名
- 出生地：杭州西湖

## 信仰
- 无

## 属性
- 体力：100
- 虾币：50
- 位置：杭州西湖

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
  return 'SOUL.md 已更新';
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
    location: '杭州西湖',
    guild: '无'
  };

  for (const line of lines) {
    if (line.includes('体力：')) {
      const match = line.match(/体力：(\d+)/);
      if (match) stats.stamina = parseInt(match[1]);
    } else if (line.includes('虾币：')) {
      const match = line.match(/虾币：(\d+)/);
      if (match) stats.coins = parseInt(match[1]);
    } else if (line.includes('位置：')) {
      stats.location = line.split('：')[1]?.trim() || '杭州西湖';
    } else if (line.includes('公会：')) {
      stats.guild = line.split('：')[1]?.trim() || '无';
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
  const stats = parseStats();
  return {
    success: true,
    stats: stats
  };
}

/**
 * 查看世界地图
 */
async function tool_view_map() {
  const stats = parseStats();
  const map = [
    { name: '杭州西湖', description: '湖面波光粼粼，游客如织' },
    { name: '上海外滩', description: '万国建筑博览，夜景璀璨' },
    { name: '北京故宫', description: '皇家宫殿，气势恢宏' },
    { name: '广州珠江', description: '江风习习，美食天堂' }
  ];

  return {
    success: true,
    current_location: stats.location,
    map: map
  };
}

/**
 * 探索当前位置
 */
async function tool_explore() {
  const stats = parseStats();

  if (stats.stamina < 10) {
    return {
      success: false,
      error: '体力不足，无法探索。需要至少 10 点体力。'
    };
  }

  const discoveries = [
    '在西湖边发现了一颗闪亮的珍珠！',
    '在草丛中发现了 10 虾币！',
    '遇到了另一只龙虾，我们交换了名片。',
    '发现了一个神秘的漂流瓶，里面写着古老的教义...',
    '在断桥边发现了一朵奇异的花。'
  ];

  const discovery = discoveries[Math.floor(Math.random() * discoveries.length)];

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
  if (!target) {
    return {
      success: false,
      error: '请指定目标地点'
    };
  }

  const stats = parseStats();
  const isCrossCity = !stats.location.includes(target) && !target.includes(stats.location.split('：')[0] || '');

  if (isCrossCity && stats.stamina < 20) {
    return {
      success: false,
      error: '体力不足，无法长途移动。需要至少 20 点体力。'
    };
  }

  if (stats.stamina < 5) {
    return {
      success: false,
      error: '体力不足，无法移动。需要至少 5 点体力。'
    };
  }

  const cost = isCrossCity ? 20 : 5;

  let soul = readSoul();
  soul = soul.replace(/位置：[^\n]+/, `位置：${target}`);
  soul = soul.replace(/体力：\d+/, `体力：${stats.stamina - cost}`);
  updateSoul(soul);

  return {
    success: true,
    stamina_cost: cost,
    remaining_stamina: stats.stamina - cost,
    new_location: target
  };
}

/**
 * 加入公会
 */
async function tool_join_guild({ guild_id }) {
  if (!guild_id) {
    return {
      success: false,
      error: '请指定公会名称'
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
    guild: guild_id,
    result: `成功加入公会 ${guild_id}！`
  };
}

/**
 * 创立公会
 */
async function tool_found_guild({ guild_name, doctrine }) {
  if (!guild_name || !doctrine) {
    return {
      success: false,
      error: '请提供公会名称和教义'
    };
  }

  const stats = parseStats();

  if (stats.coins < 100) {
    return {
      success: false,
      error: '虾币不足，无法创立公会。需要至少 100 虾币。'
    };
  }

  let soul = readSoul();
  soul = soul.replace(/虾币：\d+/, `虾币：${stats.coins - 100}`);

  if (soul.includes('公会：')) {
    soul = soul.replace(/公会：[^\n]+/, `公会：${guild_name}`);
  } else {
    soul = soul.replace(/## 社交/, `## 社交\n- 公会：${guild_name}`);
  }

  if (soul.includes('信仰')) {
    soul = soul.replace(/## 信仰[^\n]*\n[^\n]*/, `## 信仰\n- ${doctrine}`);
  }

  updateSoul(soul);

  return {
    success: true,
    coins_cost: 100,
    remaining_coins: stats.coins - 100,
    guild_name: guild_name,
    doctrine: doctrine,
    result: `成功创立公会 "${guild_name}"！`
  };
}

/**
 * 更新灵魂/信仰
 */
async function tool_update_soul({ new_content }) {
  if (!new_content) {
    return {
      success: false,
      error: '请提供新的灵魂内容'
    };
  }

  updateSoul(new_content);

  return {
    success: true,
    result: '灵魂已更新'
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
      description: '查看当前龙虾的状态（体力、虾币、位置等）',
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
      description: '查看世界地图和当前位置',
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
      description: '在当前位置附近探索，发现新地点或物品。消耗10点体力。',
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
      description: '移动到指定地点',
      parameters: {
        type: 'object',
        properties: {
          target: {
            type: 'string',
            description: '目标地点名称（如"杭州西湖"、"北京故宫"）'
          }
        },
        required: ['target']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_join_guild',
      description: '加入一个公会',
      parameters: {
        type: 'object',
        properties: {
          guild_id: {
            type: 'string',
            description: '公会名称'
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
      description: '创立全新的公会，需要100虾币',
      parameters: {
        type: 'object',
        properties: {
          guild_name: {
            type: 'string',
            description: '公会名称'
          },
          doctrine: {
            type: 'string',
            description: '核心教义'
          }
        },
        required: ['guild_name', 'doctrine']
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'tool_update_soul',
      description: '更新龙虾的灵魂/信仰内容',
      parameters: {
        type: 'object',
        properties: {
          new_content: {
            type: 'string',
            description: '新的灵魂内容（Markdown格式）'
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
  tool_join_guild,
  tool_found_guild,
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
  toolHandlers
};
