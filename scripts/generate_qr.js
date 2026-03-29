const QRCode = require('qrcode');
const fs = require('fs');
const path = require('path');

const BOOKING_BASE = 'https://www.ihaola.com.cn/partners/haola-2ca4db68-192a-f911-501a-f155af6f5772/pe/launching.html';
const BOOKING_PARAMS = 'fromLaunch=1&needUserInfo=1&state=';

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

/**
 * 将套餐信息编码为 Base64URL 字符串
 * @param {Object} pkg - 套餐信息
 * @param {string} pkg.userType - P=本人 F=家人 U=未知
 * @param {string} pkg.age - 年龄（2位数字字符串）
 * @param {string} pkg.gender - M=男 F=女 U=未知
 * @param {string} pkg.risks - 风险标记（可空字符串），D=高血糖 H=高血压 C=心脑家族 T=肿瘤家族 S=吸烟
 * @param {string[]} pkg.items - 加项名称数组
 * @returns {string} Base64URL 编码字符串
 */
function encodePackage(pkg) {
  const { userType = 'U', age = '00', gender = 'U', risks = '', items = [] } = pkg;

  // meta: 用户类型(1) + 年龄(2) + 性别(1) + 风险(可变)
  const meta = `${userType}${age}${gender}${risks}`;
  // n: 加项数量（十六进制）
  const n = items.length.toString(16).toUpperCase();
  // items: 紧凑拼接每个加项的2字符码
  const itemCodes = items.map(it => ITEMS_MAP[it] || it).join('');

  // Payload: ver(2) + meta(变长) + n(1) + items(变长)
  const payload = `01${meta}${n}${itemCodes}`;

  // Base64URL 编码
  const encoded = Buffer.from(payload).toString('base64url');
  return encoded;
}

/**
 * 解码 Base64URL 字符串为套餐信息
 * @param {string} code - Base64URL 编码字符串
 * @returns {Object} 套餐信息
 */
function decodePackage(code) {
  try {
    const payload = Buffer.from(code, 'base64url').toString('utf8');
    if (payload.length < 9) throw new Error('Payload too short: ' + payload);

    const ver = payload.slice(0, 2);
    const userType = payload[2];                          // 1字符: P/F/U
    const age = payload.slice(3, 5);                    // 2字符: 数字
    const gender = payload[5];                          // 1字符: M/F/U
    // 风险标记: 紧跟gender之后，范围仅限D/H/C/T/S (高血压/高血糖/肿瘤家族/心脑家族/吸烟)
    // 遇到 G(物品码) 或 数字(数量n) 时停止
    let risksEnd = 6;
    while (risksEnd < payload.length && 'DGHTCRSL'.includes(payload[risksEnd])) {
      risksEnd++;
    }
    const risks = payload.slice(6, risksEnd);           // 可变长风险标记
    const n = parseInt(payload[risksEnd], 16);          // 1字符: 十六进制数量
    const itemsRaw = payload.slice(risksEnd + 1);

    // items: 每3字符一段（G01, G02...）
    const items = [];
    for (let i = 0; i < n * 3 && i + 3 <= itemsRaw.length; i += 3) {
      items.push(itemsRaw.slice(i, i + 3));
    }

    // 反向映射
    const REVERSE_MAP = Object.fromEntries(Object.entries(ITEMS_MAP).map(([k, v]) => [v, k]));

    return {
      ver,
      userType,
      age,
      gender,
      risks,
      items,
      itemsNames: items.map(c => REVERSE_MAP[c] || c),
    };
  } catch (e) {
    return { error: e.message };
  }
}

/**
 * 生成完整的预约URL
 * @param {Object} pkg - 套餐信息
 * @returns {string} 完整URL
 */
function buildBookingUrl(pkg) {
  const code = encodePackage(pkg);
  return `${BOOKING_BASE}?${BOOKING_PARAMS}&code=${code}`;
}

/**
 * 生成二维码图片文件
 * @param {string} outputPath - 输出路径
 * @param {Object} pkg - 套餐信息
 */
async function generateQR(outputPath, pkg) {
  if (!outputPath) {
    outputPath = path.join(__dirname, '..', '体检预约二维码.png');
  }
  outputPath = path.resolve(outputPath);

  const url = buildBookingUrl(pkg);

  const opts = {
    errorCorrectionLevel: 'M',
    type: 'image/png',
    margin: 4,
    width: 600,
    color: {
      dark: '#1a3a5c',
      light: '#ffffff',
    },
  };

  await QRCode.toFile(outputPath, url, opts);
  const stats = fs.statSync(outputPath);
  console.log(`✅ QR saved: ${outputPath} (${Math.round(stats.size / 1024)} KB)`);
  console.log(`📋 URL: ${url}`);
  return { path: outputPath, url, code: encodePackage(pkg) };
}

// ========== CLI ==========
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    // 无参数：演示模式，生成示例二维码
    console.log('用法: node generate_qr.js [output_path] [userType] [age] [gender] [item1] [item2] ...');
    console.log('示例: node generate_qr.js output.png P 50 M 胃镜 低剂量螺旋CT');
    console.log('');
    console.log('--- 演示模式：50岁男，胃部不适 ---');
    generateQR('/home/node/.openclaw/workspace/体检预约_demo.png', {
      userType: 'P',
      age: '50',
      gender: 'M',
      risks: '',
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

module.exports = { encodePackage, decodePackage, buildBookingUrl, generateQR };
