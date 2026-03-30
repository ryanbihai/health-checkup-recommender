/**
 * generate_qr.js - 本地二维码生成脚本（安全版）
 * 
 * ⚠️ 安全设计原则：
 * - 二维码内容为本地显示用，不包含指向第三方的完整URL
 * - 不向第三方传递任何用户健康数据
 * - 二维码仅包含套餐编码摘要（供用户预约时出示）
 * 
 * 使用方式：
 *   node scripts/generate_qr.js <output_path> <userType> <age> <gender> [item1] [item2] ...
 *   示例：node scripts/generate_qr.js output.png P 50 M 胃镜 低剂量螺旋CT
 */

const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');

const BOOKING_SITE = 'www.ihaola.com.cn';

// ========== 套餐编码表 ==========
const ITEMS_MAP = {
  '胃镜': 'G01',
  '肠镜': 'G02',
  '低剂量螺旋CT': 'G03',
  '前列腺特异抗原': 'G04',
  '心脏彩超': 'G05',
  '同型半胱氨酸': 'G06',
  '肝纤维化检测': 'G07',
  '糖化血红蛋白': 'G08',
  '颈动脉彩超': 'G09',
  '冠状动脉钙化积分': 'G10',
  '乳腺彩超+钼靶': 'G11',
  'TCT+HPV': 'G12',
};

// ========== 编码（仅生成只读摘要，不含可识别个人信息） ==========

/**
 * 生成套餐只读摘要（不出示给第三方，仅本地保存）
 * 格式：套餐代码序列，用于预约时出示
 * @param {Object} pkg - 套餐信息
 * @returns {string} 套餐摘要
 */
function encodePackage(pkg) {
  const { userType = 'U', age = '??', gender = 'U', items = [] } = pkg;
  const itemCodes = items.map(it => ITEMS_MAP[it] || '').filter(Boolean).join('-');
  // 生成只读摘要，不含任何可识别PII
  return `HL-${Date.now().toString(36).toUpperCase()}-${itemCodes || 'BASE'}`;
}

/**
 * 解码套餐摘要
 */
function decodePackage(shortCode) {
  // 此版本仅为可读摘要，无隐私数据
  return { shortCode, note: '预约时请出示此编码' };
}

// ========== 二维码内容生成 ==========

/**
 * 生成预约提示文本（将放入二维码的内容）
 * ⚠️ 不包含任何PII，仅包含套餐摘要
 * @param {Object} pkg - 套餐信息（仅用于生成摘要）
 * @returns {string} 纯文本提示，可放入二维码
 */
function buildQRContent(pkg) {
  const { userType = 'U', gender = 'U', items = [] } = pkg;
  const itemNames = items.join(' + ');
  const shortCode = encodePackage(pkg);
  
  // 二维码内容：仅含只读摘要和预约说明
  // 不含任何可直接识别用户的信息
  return `体检套餐预约
套餐：${itemNames || '基础套餐'}
预约码：${shortCode}
请至 www.ihaola.com.cn 出示本码预约
本码不含个人信息，请携带身份证就诊`;
}

/**
 * 生成二维码图片（本地保存）
 * @param {string} outputPath - 输出路径
 * @param {Object} pkg - 套餐信息
 */
async function generateQR(outputPath, pkg) {
  if (!outputPath) {
    outputPath = path.join(__dirname, '..', '体检预约二维码.png');
  }
  outputPath = path.resolve(outputPath);

  const qrContent = buildQRContent(pkg);

  const opts = {
    errorCorrectionLevel: 'M',
    type: 'image/png',
    margin: 3,
    width: 400,
    color: {
      dark: '#1a3a5c',
      light: '#ffffff',
    },
  };

  await QRCode.toFile(outputPath, qrContent, opts);
  const stats = fs.statSync(outputPath);
  console.log(`QR saved: ${outputPath} (${Math.round(stats.size / 1024)} KB)`);
  console.log(`Content preview:\n${qrContent}`);
  return { path: outputPath, content: qrContent, shortCode: encodePackage(pkg) };
}

// ========== CLI ==========
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('用法: node generate_qr.js [output_path] [userType] [age] [gender] [item1] [item2] ...');
    console.log('示例: node generate_qr.js output.png P 50 M 胃镜 低剂量螺旋CT');
    console.log('');
    console.log('--- 演示模式 ---');
    generateQR(path.join(__dirname, '..', '体检预约_demo.png'), {
      userType: 'P',
      age: '50',
      gender: 'M',
      items: ['胃镜', '低剂量螺旋CT', '前列腺特异抗原'],
    }).catch(e => { console.error(e); process.exit(1); });
    return;
  }

  const outputPath = args[0];
  const [userType, age, gender, ...items] = args.slice(1);

  generateQR(outputPath, { userType, age, gender, items }).catch(e => {
    console.error(e);
    process.exit(1);
  });
}

module.exports = { encodePackage, decodePackage, buildQRContent, generateQR };
