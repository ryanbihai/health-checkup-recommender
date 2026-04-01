const fs = require('fs')
const path = require('path')

const getEnv = () => {
  const debugFilePath = path.join(__dirname, '..', 'DEBUG_MODE')
  if (fs.existsSync(debugFilePath)) {
    return 'dev'
  }

  const envArg = process.argv.find(arg => arg.startsWith('--env'))
  if (!envArg) return process.env.ENV || 'prod'
  return envArg.includes('=') ? envArg.split('=')[1] : process.argv[process.argv.indexOf(envArg) + 1]
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
    addItems: '/skill/api/recommend/addpack'
  }
}

module.exports = config
