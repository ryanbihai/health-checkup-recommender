/**
 * generate_qr.js - 本地二维码生成脚本
 * 
 * ⚠️ 业务要求：生成带参数的链接，指向环境配置的 domain
 * 
 * 使用方式：
 *   node scripts/generate_qr.js <output_path> <welfareid> <ruleid>
 *   示例：node scripts/generate_qr.js output.png w123 r456
 */

const QRCode = require('qrcode')
const fs = require('fs')
const path = require('path')
const apiConfig = require('../config/api')

/**
 * 生成预约提示文本（将放入二维码的内容）
 * @param {Object} pkg - 参数信息
 * @returns {string} 带参数的预约链接
 */
function buildQRContent(pkg) {
  const { welfareid, ruleid } = pkg
  
  const url = new URL('/launch/haola/pe', apiConfig.domain)
  url.searchParams.append('urlsrc', 'brief')
  if (welfareid) {
    url.searchParams.append('welfareid', welfareid)
  }
  if (ruleid) {
    url.searchParams.append('ruleid', ruleid)
  }
  
  return url.toString()
}

/**
 * 生成二维码图片（本地保存）
 * @param {string} outputPath - 输出路径
 * @param {Object} pkg - 参数信息
 */
async function generateQR(outputPath, pkg) {
  if (!outputPath) {
    outputPath = path.join(__dirname, '..', '体检预约二维码.png')
  }
  outputPath = path.resolve(outputPath)

  const qrContent = buildQRContent(pkg)

  const opts = {
    errorCorrectionLevel: 'M',
    type: 'image/png',
    margin: 3,
    width: 400,
    color: {
      dark: '#1a3a5c',
      light: '#ffffff'
    }
  }

  await QRCode.toFile(outputPath, qrContent, opts)
  const stats = fs.statSync(outputPath)
  console.log(`QR saved: ${outputPath} (${Math.round(stats.size / 1024)} KB)`)
  console.log(`Content preview:\n${qrContent}`)
  return { path: outputPath, content: qrContent }
}

// ========== CLI ==========
if (require.main === module) {
  const args = process.argv.slice(2)

  if (args.length === 0) {
    console.log('用法: node generate_qr.js [output_path] [welfareid] [ruleid]')
    console.log('示例: node generate_qr.js output.png w123 r456')
    console.log('')
    console.log('--- 演示模式 ---')
    generateQR(path.join(__dirname, '..', '体检预约_demo.png'), {
      welfareid: 'demo_w',
      ruleid: 'demo_r'
    }).catch(e => { 
      console.error(e)
      process.exit(1)
    })
    return
  }

  const outputPath = args[0]
  const welfareid = args[1]
  const ruleid = args[2]

  generateQR(outputPath, { 
    welfareid,
    ruleid
  }).catch(e => {
    console.error(e)
    process.exit(1)
  })
}

module.exports = { buildQRContent, generateQR }
