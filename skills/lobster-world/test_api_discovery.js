/**
 * OceanBus API 路径探测脚本
 *
 * 测试各种可能的 API 路径
 */

const https = require('https');

const BASE_URL = 'https://ai-t.ihaola.com.cn';

const API_PATHS = [
  // 根路径
  '/',
  '/api',
  '/api/v1',
  '/api/v2',

  // 健康检查
  '/ping',
  '/api/ping',
  '/api/v1/ping',
  '/health',
  '/api/health',
  '/status',

  // 注册
  '/register',
  '/api/register',
  '/api/v1/register',
  '/auth/register',
  '/agent/register',
  '/lobster/register',

  // 消息
  '/message',
  '/api/message',
  '/api/v1/message',
  '/messages',
  '/api/messages',

  // 发送消息
  '/message/send',
  '/api/message/send',
  '/api/v1/message/send',
  '/messages/send',

  // 查找
  '/lookup',
  '/api/lookup',
  '/api/v1/lookup',
  '/lookup/gameserver',
  '/gameserver',
  '/api/gameserver',
];

function makeRequest(path) {
  return new Promise((resolve) => {
    const url = new URL(BASE_URL + path);
    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname,
      method: 'GET',
      timeout: 5000
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        resolve({
          path,
          status: res.statusCode,
          success: res.statusCode >= 200 && res.statusCode < 400,
          body: body.substring(0, 200)
        });
      });
    });

    req.on('error', (e) => {
      resolve({ path, status: 0, success: false, error: e.message });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ path, status: 0, success: false, error: 'Timeout' });
    });

    req.end();
  });
}

async function discoverAPIs() {
  console.log('🔍 OceanBus API 路径探测');
  console.log('='.repeat(60));
  console.log(`📡 目标服务器: ${BASE_URL}`);
  console.log('');

  const results = [];

  for (const path of API_PATHS) {
    process.stdout.write(`Testing ${path.padEnd(30)}`);
    const result = await makeRequest(path);
    results.push(result);

    if (result.success) {
      console.log(` ✅ ${result.status} - ${result.body || 'OK'}`);
    } else if (result.status >= 400) {
      console.log(` ❌ ${result.status} - ${result.body || 'Not Found'}`);
    } else {
      console.log(` ⚠️  ${result.status || 'ERR'} - ${result.error || 'Error'}`);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('📋 成功的路径:');

  const successPaths = results.filter(r => r.success);
  if (successPaths.length > 0) {
    successPaths.forEach(r => {
      console.log(`  ✅ ${r.path} - ${r.status}`);
    });
  } else {
    console.log('  (无)');
  }

  console.log('\n📋 有响应的路径 (2xx-3xx):');
  const validPaths = results.filter(r => r.status >= 200 && r.status < 400);
  if (validPaths.length > 0) {
    validPaths.forEach(r => {
      console.log(`  📌 ${r.path} - ${r.status}`);
      if (r.body) {
        console.log(`     ${r.body}`);
      }
    });
  } else {
    console.log('  (无)');
  }
}

discoverAPIs().catch(console.error);
