const fs = require('fs')
const path = require('path')

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

const getEnv = () => {
  const envFilePath = path.join(__dirname, '..', '.env')
  if (fs.existsSync(envFilePath) || process.env.NODE_ENV === 'development') {
    return 'dev'
  }
  return 'prod'
}

const activeEnv = envMap[getEnv()] || envMap.prod

const config = {
  domain: activeEnv.domain,
  baseUrl: activeEnv.baseUrl,
  api: {
    addItems: '/skill/api/recommend/addpack'
  }
}

module.exports = config
