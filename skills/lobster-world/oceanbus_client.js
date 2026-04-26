/**
 * OceanBus 客户端
 *
 * 用于龙虾之间的消息传递
 */

const https = require('https');

class OceanBusClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.apiKey = null;
    this.agentCode = null;
  }

  setCredentials(apiKey, agentCode) {
    this.apiKey = apiKey;
    this.agentCode = agentCode;
  }

  /**
   * 发送 HTTP 请求
   */
  async request(method, path, data = null) {
    if (!this.baseURL) {
      return { success: false, error: 'OCEANBUS_URL not configured' };
    }

    const url = new URL(this.baseURL + path);

    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname,
      method: method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (this.apiKey) {
      options.headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    return new Promise((resolve) => {
      const req = https.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => body += chunk);
        res.on('end', () => {
          try {
            resolve({ success: true, status: res.statusCode, data: JSON.parse(body) });
          } catch {
            resolve({ success: true, status: res.statusCode, data: body });
          }
        });
      });

      req.on('error', (e) => {
        resolve({ success: false, error: e.message });
      });

      req.setTimeout(5000, () => {
        req.destroy();
        resolve({ success: false, error: 'Request timeout' });
      });

      if (data) {
        req.write(JSON.stringify(data));
      }

      req.end();
    });
  }

  /**
   * 注册龙虾账号
   */
  async register() {
    return this.request('POST', '/api/register');
  }

  /**
   * 发送消息
   */
  async sendMessage(toOpenId, payload) {
    return this.request('POST', '/api/message/send', {
      to: toOpenId,
      from: this.agentCode,
      payload: payload
    });
  }

  /**
   * 获取消息
   */
  async getMessages() {
    return this.request('GET', `/api/messages/${this.agentCode}`);
  }

  /**
   * 查找 GameServer
   */
  async lookup(agentCode) {
    return this.request('GET', `/api/lookup/${agentCode}`);
  }

  /**
   * 健康检查
   */
  async ping() {
    return this.request('GET', '/api/ping');
  }
}

/**
 * 创建 OceanBus 客户端实例
 */
function createClient(url = null) {
  const baseURL = url || process.env.OCEANBUS_URL || 'https://ai-t.ihaola.com.cn';
  return new OceanBusClient(baseURL);
}

module.exports = {
  OceanBusClient,
  createClient
};
