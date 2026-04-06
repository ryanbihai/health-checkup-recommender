const envMap = {
  dev: {
    domain: 'https://t.ihaola.com.cn',
    baseUrl: 'https://pe-t.ihaola.com.cn'
  },
  prod: {
    domain: 'https://www.ihaola.com.cn',
    baseUrl: 'https://pe.ihaola.com.cn'
  }
}

// 移除了 DEBUG_MODE 文件读取逻辑，以满足安全合规要求。
// 现在完全通过标准环境变量控制环境
const activeEnv = process.env.NODE_ENV === 'development' ? envMap.dev : envMap.prod

const config = {
  domain: activeEnv.domain,
  baseUrl: activeEnv.baseUrl,
  api: {
    addItems: '/skill/api/recommend/addpack'
  }
}

module.exports = config
