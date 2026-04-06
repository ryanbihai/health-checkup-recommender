const getEnv = () => {
  if (process.env.NODE_ENV === 'development') {
    return 'dev'
  }

  return 'prod'
}

const envMap = {
  dev: {
    domain: 'https://t.ihaola.com.cn',
    baseUrl: 'https://pe-t.ihaola.com.cn'
  },
  prod: {
    domain: 'https://t.ihaola.com.cn',
    baseUrl: 'https://pe-t.ihaola.com.cn'
  }
}

const activeEnv = envMap[getEnv()] || envMap.prod

const config = {
  domain: activeEnv.domain,
  baseUrl: activeEnv.baseUrl,
  api: {
    addItems: '/skill/api/recommend/addpack',
    sendMessage: '/skill/api/send_message',
    getReply: '/skill/api/get_reply'
  }
}

module.exports = config
