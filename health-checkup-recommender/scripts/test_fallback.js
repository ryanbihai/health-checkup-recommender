#!/usr/bin/env node
/**
 * test_fallback.js - 测试二维码生成降级机制
 *
 * 演示在接口正常和接口失败两种情况下的行为
 */

const path = require('path')
const { smartGenerateQR, DEFAULT_WELFARE_ID, DEFAULT_RULE_ID } = require('./generate_qr_with_fallback')

console.log('\n========================================')
console.log('🧪 测试二维码生成降级机制')
console.log('========================================\n')

console.log('测试项目: Item029, Item131, Item173, Item032')
console.log('默认参数:')
console.log(`  welfareid: ${DEFAULT_WELFARE_ID}`)
console.log(`  ruleid: ${DEFAULT_RULE_ID}`)
console.log('')

const outputPath = path.join(__dirname, '..', 'test_fallback_demo.png')

smartGenerateQR(outputPath, ['Item029', 'Item131', 'Item173', 'Item032'])
  .then(result => {
    console.log('\n========================================')
    console.log('📊 测试结果')
    console.log('========================================')
    console.log(`状态: ${result.fallback ? '⚠️ 降级模式（使用默认参数）' : '✅ 个性化模式（使用接口参数）'}`)
    console.log(`来源: ${result.source}`)
    console.log(`路径: ${result.path}`)
    console.log(`内容: ${result.content}`)
    console.log('========================================\n')

    if (result.fallback) {
      console.log('💡 说明：接口调用失败，已自动降级为默认二维码')
      console.log('   用户仍可扫码预约，但需在页面手动选择体检项目')
    } else {
      console.log('✅ 说明：接口调用成功，已生成个性化二维码')
    }

    process.exit(0)
  })
  .catch(error => {
    console.error('\n❌ 测试失败:', error.message)
    process.exit(1)
  })
