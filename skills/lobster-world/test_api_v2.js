/**
 * OceanBus API 探测 v2 - 更多路径
 */

const https = require('https');

const BASE_URL = 'https://ai-t.ihaola.com.cn';

async function makeRequest(method, path, data = null) {
  return new Promise((resolve) => {
    const url = new URL(BASE_URL + path);
    const body = data ? JSON.stringify(data) : null;

    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname,
      method: method,
      headers: {},
      timeout: 5000
    };

    if (body) {
      options.headers['Content-Type'] = 'application/json';
      options.headers['Content-Length'] = Buffer.byteLength(body);
    }

    const req = https.request(options, (res) => {
      let responseBody = '';
      res.on('data', (chunk) => responseBody += chunk);
      res.on('end', () => {
        resolve({
          method,
          path,
          status: res.statusCode,
          success: res.statusCode >= 200 && res.statusCode < 400,
          body: responseBody.substring(0, 300)
        });
      });
    });

    req.on('error', (e) => resolve({ method, path, status: 0, success: false, error: e.message }));
    req.on('timeout', () => { req.destroy(); resolve({ method, path, status: 0, success: false, error: 'Timeout' }); });

    if (body) req.write(body);
    req.end();
  });
}

async function test() {
  console.log('🔍 OceanBus API 探测 v2');
  console.log('='.repeat(60));

  const tests = [
    // 基于服务器响应格式的猜测
    ['GET', '/api/agent/ping'],
    ['GET', '/api/lobster/ping'],
    ['GET', '/api/game/ping'],
    ['GET', '/api/server/ping'],
    ['GET', '/api/gameserver/ping'],

    // 认证相关
    ['POST', '/api/auth/login'],
    ['POST', '/api/auth/register'],
    ['POST', '/api/session/create'],

    // 龙虾相关
    ['POST', '/api/agent/register'],
    ['POST', '/api/agent/login'],
    ['POST', '/api/lobster/register'],
    ['GET', '/api/agent/info'],
    ['GET', '/api/lobster/info'],

    // 游戏相关
    ['POST', '/api/game/action'],
    ['POST', '/api/game/register'],
    ['GET', '/api/game/status'],

    // 消息相关
    ['POST', '/api/msg/send'],
    ['POST', '/api/chat/send'],
    ['GET', '/api/msg/inbox'],
  ];

  for (const [method, path] of tests) {
    process.stdout.write(`${method.padEnd(6)} ${path.padEnd(25)}`);
    const result = await makeRequest(method, path);
    if (result.success || (result.status >= 200 && result.status < 400)) {
      console.log(` ✅ ${result.status} - ${result.body}`);
    } else {
      console.log(` ❌ ${result.status}`);
    }
  }
}

test().catch(console.error);
