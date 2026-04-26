/**
 * OceanBus API 路径探测 - POST 请求
 */

const https = require('https');

const BASE_URL = 'https://ai-t.ihaola.com.cn';

async function postRequest(path, data) {
  return new Promise((resolve) => {
    const url = new URL(BASE_URL + path);
    const body = JSON.stringify(data);

    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 5000
    };

    const req = https.request(options, (res) => {
      let responseBody = '';
      res.on('data', (chunk) => responseBody += chunk);
      res.on('end', () => {
        resolve({
          path,
          method: 'POST',
          status: res.statusCode,
          success: res.statusCode >= 200 && res.statusCode < 400,
          body: responseBody.substring(0, 300)
        });
      });
    });

    req.on('error', (e) => {
      resolve({ path, method: 'POST', status: 0, success: false, error: e.message });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ path, method: 'POST', status: 0, success: false, error: 'Timeout' });
    });

    req.write(body);
    req.end();
  });
}

async function discoverPOST() {
  console.log('🔍 OceanBus API 探测 - POST 请求');
  console.log('='.repeat(60));
  console.log(`📡 目标服务器: ${BASE_URL}`);
  console.log('');

  const testCases = [
    { path: '/api/register', data: { name: 'test_lobster' } },
    { path: '/api/agent/register', data: { name: 'test_lobster' } },
    { path: '/api/lobster/register', data: { name: 'test_lobster' } },
    { path: '/register', data: { name: 'test_lobster' } },
    { path: '/api/message/send', data: { to: 'test', text: 'hello' } },
    { path: '/api/agent/message', data: { to: 'test', text: 'hello' } },
    { path: '/api/lobster/message', data: { to: 'test', text: 'hello' } },
    { path: '/api/gameserver/lookup', data: { agent_code: 'test' } },
    { path: '/api/agent/lookup', data: { agent_code: 'test' } },
    { path: '/api/ping', data: {} },  // POST ping
    { path: '/health', data: {} },  // POST health
  ];

  for (const tc of testCases) {
    process.stdout.write(`POST ${tc.path.padEnd(30)}`);
    const result = await postRequest(tc.path, tc.data);
    if (result.success) {
      console.log(` ✅ ${result.status} - ${result.body}`);
    } else {
      console.log(` ❌ ${result.status} - ${result.body || result.error}`);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('🏁 探测完成');
}

discoverPOST().catch(console.error);
