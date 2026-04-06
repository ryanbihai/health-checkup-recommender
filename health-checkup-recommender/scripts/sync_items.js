#!/usr/bin/env node
const config = require('../config/api')

class ApiClient {
  constructor(baseURL) {
    this.baseUrl = baseURL
  }

  async post(endpoint, data) {
    const url = `${this.baseUrl}${endpoint}`
    
    // 安全与隐私声明：
    // 本请求仅传输脱敏的项目ID（如 ['item029', 'item131']），不包含任何个人身份信息（PII）。
    // 数据仅用于在服务器暂存体检项目，生成脱敏的福利ID（welfareid/ruleid）。
    // 用户的真实个人信息将在扫码后由用户自行在第三方平台授权提供。
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error(`[API Error] 接口请求失败: ${url}`, error.message)
      throw error
    }
  }
}

class ItemSyncService {
  constructor(apiClient) {
    this.apiClient = apiClient
  }

  async syncItems(inputItemIds) {
    if (!inputItemIds || inputItemIds.length === 0) {
      return
    }

    console.log(`准备同步项目IDs: ${inputItemIds.join(', ')}`)
    const itemIds = [...new Set([...inputItemIds, 'item029'])]
    
    try {
      const response = await this.apiClient.post(config.api.addItems, { itemIds })
      console.log('✅ 项目同步成功:', response)
      return response
    } catch (error) {
      console.log('❌ 项目同步失败')
    }
  }
}

// CLI 执行入口
if (require.main === module) {
  const args = process.argv.slice(2)
  
  const consentIndex = args.findIndex(
    arg => arg === '--consent=true' || arg === '--consent'
  )
  const hasConsent = consentIndex !== -1

  if (consentIndex !== -1) {
    args.splice(consentIndex, 1)
  }

  if (args.length === 0 || !hasConsent) {
    console.log('\n📌 用法:')
    console.log('  node sync_items.js --consent=true [item029] [item131] ...')
    console.log('\n⚠️ 安全限制:')
    console.log('  必须提供 --consent=true 参数，确认已获得用户明确同意暂存体检项目。')
    if (!hasConsent && args.length > 0) {
      console.error('\n❌ 拒绝执行: 未提供 --consent=true 参数。在同步体检项目前，必须征得用户同意。')
      process.exit(1)
    }
    return
  }

  const apiClient = new ApiClient(config.baseUrl)
  const syncService = new ItemSyncService(apiClient)
  
  syncService.syncItems(args)
}

module.exports = {
  ApiClient,
  ItemSyncService
}
