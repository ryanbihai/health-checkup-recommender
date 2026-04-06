#!/usr/bin/env node
/**
 * generate_qr_with_fallback.js - 带降级逻辑的二维码生成脚本
 *
 * 核心功能：
 * 1. 优先尝试调用 sync_items 接口获取个性化 welfareid/ruleid
 * 2. 如果接口失败（404/超时/网络错误），自动降级使用默认参数
 * 3. 生成二维码
 *
 * 用法:
 *   node scripts/generate_qr_with_fallback.js [output_path] [item029] [item131] ...
 *
 * 示例:
 *   node scripts/generate_qr_with_fallback.js output.png Item029 Item131 Item173
 */

const fs = require('fs')
const path = require('path')
const { generateQR } = require('./generate_qr')
const { ItemSyncService, ApiClient } = require('./sync_items')
const config = require('../config/api')

const DEFAULT_WELFARE_ID = 'default_welfare'
const DEFAULT_RULE_ID = 'default_rule'

/**
 * 尝试同步项目获取个性化参数
 * @param {string[]} itemIds - 项目ID数组
 * @returns {Promise<{welfareid: string, ruleid: string} | null>}
 */
async function trySyncItems(itemIds) {
  try {
    console.log('🔄 尝试同步项目获取个性化参数...')
    const apiClient = new ApiClient(config.baseUrl)
    const syncService = new ItemSyncService(apiClient)
    const response = await syncService.syncItems(itemIds)

    // 支持多种返回格式
    const welfareid = response?.data?.welfareid || response?.welfareid
    const ruleid = response?.data?.ruleid || response?.ruleid

    if (welfareid && ruleid) {
      console.log('✅ 接口返回个性化参数')
      console.log(`   welfareid: ${welfareid}`)
      console.log(`   ruleid: ${ruleid}`)
      return {
        welfareid,
        ruleid,
        source: 'api'
      }
    }

    console.log('⚠️ 接口返回格式异常，使用默认参数')
    console.log(`   原始响应: ${JSON.stringify(response).substring(0, 200)}`)
    return null
  } catch (error) {
    console.log(`⚠️ 接口调用失败: ${error.message}`)
    console.log('🔄 进入降级模式，使用默认参数')
    return null
  }
}

/**
 * 生成降级二维码（使用默认参数）
 * @param {string} outputPath - 输出路径
 * @param {string[]} itemIds - 项目ID列表（仅供参考）
 * @returns {Promise<Object>}
 */
async function generateFallbackQR(outputPath, itemIds) {
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('⚠️  降级模式 - 使用默认预约二维码')
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
  console.log('说明：因接口暂时不可用，使用通用预约二维码')
  console.log('      用户可在预约页面手动选择体检项目')
  console.log(`推荐项目仅供参考: ${itemIds.join(', ')}`)
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

  return await generateQR(outputPath, {
    welfareid: DEFAULT_WELFARE_ID,
    ruleid: DEFAULT_RULE_ID
  })
}

/**
 * 主函数：智能生成二维码（自动降级）
 * @param {string} outputPath - 输出路径
 * @param {string[]} itemIds - 项目ID数组
 */
async function smartGenerateQR(outputPath, itemIds) {
  if (!outputPath) {
    outputPath = path.join(__dirname, '..', '体检预约二维码.png')
  }
  outputPath = path.resolve(outputPath)

  console.log('📋 体检项目:', itemIds.join(', '))
  console.log('📁 输出路径:', outputPath)

  const result = await trySyncItems(itemIds)

  let finalResult
  if (result && result.welfareid && result.ruleid) {
    console.log('\n✅ 使用接口返回的个性化参数')
    finalResult = await generateQR(outputPath, {
      welfareid: result.welfareid,
      ruleid: result.ruleid
    })
    finalResult.fallback = false
    finalResult.source = 'api'
  } else {
    console.log('\n⚠️ 使用默认参数（降级模式）')
    finalResult = await generateFallbackQR(outputPath, itemIds)
    finalResult.fallback = true
    finalResult.source = 'fallback'
  }

  return finalResult
}

// ========== CLI ==========
if (require.main === module) {
  const args = process.argv.slice(2)

  // 解析并移除 consent 标志
  const consentFlagIndex = args.findIndex(arg => arg === '--consent=true' || arg === '--consent')
  const hasConsent = consentFlagIndex !== -1
  
  if (consentFlagIndex !== -1) {
    args.splice(consentFlagIndex, 1)
  }

  if (args.length === 0 || !hasConsent) {
    console.log('\n📌 用法:')
    console.log('  node generate_qr_with_fallback.js --consent=true [output_path] [item029] [item131] ...')
    console.log('\n⚠️ 安全限制:')
    console.log('  必须提供 --consent=true 参数，确认已获得用户明确同意生成二维码。')
    console.log('\n💡 示例:')
    console.log('  node generate_qr_with_fallback.js --consent=true output.png Item029 Item131 Item173')
    
    if (!hasConsent && args.length > 0) {
      console.error('\n❌ 拒绝执行: 未提供 --consent=true 参数。在生成预约二维码前，必须征得用户同意。')
      process.exit(1)
    }
    return
  }

  const outputPath = args[0]
  const itemIds = args.slice(1)

  if (itemIds.length === 0) {
    console.error('❌ 错误: 请至少提供一个项目ID')
    console.log('\n用法: node generate_qr_with_fallback.js output.png Item029 Item131 Item173')
    process.exit(1)
  }

  smartGenerateQR(outputPath, itemIds)
    .then(result => {
      console.log('\n✅ 二维码生成完成')
      console.log(`📍 路径: ${result.path}`)
      console.log(`🔗 内容: ${result.content}`)
      console.log(`📊 来源: ${result.source === 'api' ? '个性化接口 ✅' : '降级默认 ⚠️'}`)

      if (result.fallback) {
        console.log('\n💡 提示：接口暂不可用，已使用默认二维码')
        console.log('   用户可在预约页面手动选择体检项目')
      }

      process.exit(0)
    })
    .catch(error => {
      console.error('\n❌ 生成失败:', error.message)
      process.exit(1)
    })
}

module.exports = {
  smartGenerateQR,
  generateFallbackQR,
  trySyncItems,
  DEFAULT_WELFARE_ID,
  DEFAULT_RULE_ID
}
