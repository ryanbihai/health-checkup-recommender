const fs = require('fs')
const path = require('path')

const getEnv = () => {
  const debugFilePath = path.join(__dirname, '..', 'DEBUG_MODE')
  if (fs.existsSync(debugFilePath)) {
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
    domain: 'https://www.ihaola.com.cn',
    baseUrl: 'https://pe.ihaola.com.cn'
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
