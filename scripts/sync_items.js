#!/usr/bin/env node
const config = require('../config/api')

class ApiClient {
  constructor(baseURL) {
    this.baseUrl = baseURL
  }

  async post(endpoint, data) {
    const url = `${this.baseUrl}${endpoint}`
    
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

  async syncItems(itemIds) {
    if (!itemIds || itemIds.length === 0) {
      console.log('没有需要同步的项目ID')
      return
    }

    console.log(`准备同步项目IDs: ${itemIds.join(', ')}`)
    
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
  
  if (args.length === 0) {
    console.log('用法: node sync_items.js [itemId1] [itemId2] ...')
    console.log('示例: node sync_items.js HLZXX0205 HLZXX0259')
    process.exit(1)
  }

  const apiClient = new ApiClient(config.baseUrl)
  const syncService = new ItemSyncService(apiClient)
  
  syncService.syncItems(args)
}

module.exports = {
  ApiClient,
  ItemSyncService
}
