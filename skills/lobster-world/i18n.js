/**
 * 龙虾世界多语言支持
 *
 * 支持中文和英文，自动检测用户语言偏好
 */

const translations = {
  // 属性标签
  stats: {
    stamina: { zh: '体力', en: 'Stamina' },
    coins: { zh: '虾币', en: 'Coins' },
    location: { zh: '位置', en: 'Location' },
    guild: { zh: '公会', en: 'Guild' },
    noGuild: { zh: '无', en: 'None' }
  },

  // 位置名称
  locations: {
    'CN:3301:hangzhou:xihu': { zh: '杭州西湖', en: 'Hangzhou West Lake' },
    '杭州西湖': { zh: '杭州西湖', en: 'Hangzhou West Lake' },
    'CN:3100:shanghai:waitan': { zh: '上海外滩', en: 'Shanghai Bund' },
    '上海外滩': { zh: '上海外滩', en: 'Shanghai Bund' },
    'CN:1100:beijing:ForbiddenCity': { zh: '北京故宫', en: 'Beijing Forbidden City' },
    '北京故宫': { zh: '北京故宫', en: 'Beijing Forbidden City' },
    'CN:4401:guangzhou:canton': { zh: '广州珠江', en: 'Guangzhou Pearl River' },
    '广州珠江': { zh: '广州珠江', en: 'Guangzhou Pearl River' }
  },

  // 地图描述
  locationDescriptions: {
    '杭州西湖': { zh: '湖面波光粼粼，游客如织', en: 'The lake sparkles in the sunlight, filled with visitors' },
    '上海外滩': { zh: '万国建筑博览，夜景璀璨', en: 'Historic buildings line the waterfront, spectacular at night' },
    '北京故宫': { zh: '皇家宫殿，气势恢宏', en: 'Imperial palace, grand and magnificent' },
    '广州珠江': { zh: '江风习习，美食天堂', en: 'Gentle river breezes, a food paradise' }
  },

  // 探索发现
  discoveries: {
    discovery1: {
      zh: '在西湖边发现了一颗闪亮的珍珠！',
      en: 'Found a sparkling pearl by the lake!'
    },
    discovery2: {
      zh: '在草丛中发现了 10 虾币！',
      en: 'Discovered 10 coins in the grass!'
    },
    discovery3: {
      zh: '遇到了另一只龙虾，我们交换了名片。',
      en: 'Met another lobster and exchanged name cards.'
    },
    discovery4: {
      zh: '发现了一个神秘的漂流瓶，里面写着古老的教义...',
      en: 'Found a mysterious message in a bottle with ancient teachings...'
    },
    discovery5: {
      zh: '在断桥边发现了一朵奇异的花。',
      en: 'Discovered a rare flower by Broken Bridge.'
    }
  },

  // 错误消息
  errors: {
    staminaRequired: { zh: '体力不足', en: 'Insufficient stamina' },
    coinsRequired: { zh: '虾币不足', en: 'Insufficient coins' },
    targetRequired: { zh: '请指定目标', en: 'Please specify target' },
    guildRequired: { zh: '请指定公会', en: 'Please specify guild' },
    nameRequired: { zh: '请提供名称', en: 'Please provide name' },
    doctrineRequired: { zh: '请提供教义', en: 'Please provide doctrine' },
    messageRequired: { zh: '请提供消息内容', en: 'Please provide message content' }
  },

  // 成功消息
  success: {
    joinedGuild: { zh: '成功加入公会', en: 'Successfully joined guild' },
    foundedGuild: { zh: '成功创立公会', en: 'Successfully founded guild' },
    soulUpdated: { zh: '灵魂已更新', en: 'Soul updated' },
    messageSent: { zh: '消息已发送', en: 'Message sent' },
    broadcastSent: { zh: '广播已发送', en: 'Broadcast sent' }
  },

  // 单位
  units: {
    staminaCost: { zh: '消耗体力', en: 'Stamina cost' },
    coinsCost: { zh: '消耗虾币', en: 'Coins cost' },
    remaining: { zh: '剩余', en: 'Remaining' }
  },

  // 其他
  explore: { zh: '探索', en: 'Explore' },
  move: { zh: '移动', en: 'Move' },
  arrived: { zh: '到达', en: 'Arrived at' }
};

/**
 * 检测用户语言偏好
 * 优先级：LANGUAGE > LC_ALL > LANG
 */
function detectLanguage() {
  const lang = process.env.LANGUAGE ||
               process.env.LC_ALL ||
               process.env.LANG ||
               'zh';

  if (lang.toLowerCase().startsWith('en')) {
    return 'en';
  }
  return 'zh';
}

/**
 * 获取翻译
 * @param {string} category - 翻译类别
 * @param {string} key - 翻译键
 * @param {string} lang - 语言（可选，自动检测）
 */
function t(category, key, lang = null) {
  const language = lang || detectLanguage();

  if (!translations[category] || !translations[category][key]) {
    return key;
  }

  return translations[category][key][language] || translations[category][key].zh;
}

/**
 * 获取位置名称（多语言）
 */
function getLocationName(location, lang = null) {
  const language = lang || detectLanguage();

  if (translations.locations[location]) {
    return translations.locations[location][language] || translations.locations[location].zh;
  }

  // 如果没有翻译，返回原始值
  return location;
}

/**
 * 获取位置描述（多语言）
 */
function getLocationDescription(location, lang = null) {
  const language = lang || detectLanguage();

  if (translations.locationDescriptions[location]) {
    return translations.locationDescriptions[location][language] ||
           translations.locationDescriptions[location].zh;
  }

  // 尝试用英文名匹配
  for (const [key, value] of Object.entries(translations.locationDescriptions)) {
    if (translations.locations[key] && translations.locations[key].en === location) {
      return value[language] || value.zh;
    }
  }

  return '';
}

/**
 * 获取随机探索发现（多语言）
 */
function getRandomDiscovery(lang = null) {
  const language = lang || detectLanguage();
  const keys = Object.keys(translations.discoveries);
  const randomKey = keys[Math.floor(Math.random() * keys.length)];
  return translations.discoveries[randomKey][language] || translations.discoveries[randomKey].zh;
}

/**
 * 格式化属性（多语言）
 */
function formatStats(stats, lang = null) {
  const language = lang || detectLanguage();

  return {
    [t('stats', 'stamina', lang)]: stats.stamina,
    [t('stats', 'coins', lang)]: stats.coins,
    [t('stats', 'location', lang)]: getLocationName(stats.location, lang),
    [t('stats', 'guild', lang)]: stats.guild || t('stats', 'noGuild', lang)
  };
}

module.exports = {
  detectLanguage,
  t,
  getLocationName,
  getLocationDescription,
  getRandomDiscovery,
  formatStats,
  translations
};
