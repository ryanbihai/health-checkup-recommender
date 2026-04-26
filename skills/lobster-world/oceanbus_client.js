/**
 * OceanBus 客户端
 *
 * 用于龙虾之间的消息传递
 * API 文档: /api/l0/
 */

const https = require('https');

class OceanBusClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.apiKey = null;
    this.agentCode = null;
    this.agentId = null;
    this.lastSeq = 0;
  }

  setCredentials(apiKey, agentCode) {
    this.apiKey = apiKey;
    this.agentCode = agentCode;
  }

  /**
   * 发送 HTTP 请求
   */
  async request(method, path, body = null) {
    if (!this.baseURL) {
      return { success: false, error: 'OCEANBUS_URL not configured' };
    }

    const url = new URL(this.baseURL + path);

    const options = {
      hostname: url.hostname,
      port: url.port || 443,
      path: url.pathname + url.search,
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
        let responseBody = '';
        res.on('data', (chunk) => responseBody += chunk);
        res.on('end', () => {
          try {
            const data = JSON.parse(responseBody);
            resolve({
              success: res.statusCode >= 200 && res.statusCode < 300,
              status: res.statusCode,
              data: data
            });
          } catch {
            resolve({
              success: res.statusCode >= 200 && res.statusCode < 300,
              status: res.statusCode,
              data: responseBody
            });
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

      if (body) {
        req.write(JSON.stringify(body));
      }

      req.end();
    });
  }

  /**
   * 注册新 Agent (发牌)
   * POST /api/l0/agents/register
   */
  async register(agentName = 'lobster') {
    return this.request('POST', '/api/l0/agents/register', {
      name: agentName
    });
  }

  /**
   * 精确寻址 - 通过 agent_code 查找 openid
   * GET /api/l0/agents/lookup?agent_code=xxx
   */
  async lookup(agentCode) {
    return this.request('GET', `/api/l0/agents/lookup?agent_code=${encodeURIComponent(agentCode)}`);
  }

  /**
   * 发送消息
   * POST /api/l0/messages
   */
  async sendMessage(toOpenid, content, clientMsgId = null) {
    const body = {
      to_openid: toOpenid,
      content: content
    };

    if (clientMsgId) {
      body.client_msg_id = clientMsgId;
    }

    return this.request('POST', '/api/l0/messages', body);
  }

  /**
   * 同步信箱
   * GET /api/l0/messages/sync?since_seq=xxx&limit=xxx
   */
  async syncMessages(sinceSeq = 0, limit = 20) {
    return this.request('GET', `/api/l0/messages/sync?since_seq=${sinceSeq}&limit=${limit}`);
  }

  /**
   * 健康检查 (Ping)
   * GET /api/ping (兼容旧版)
   */
  async ping() {
    const result = await this.request('GET', '/api/ping');
    if (!result.success) {
      return this.request('GET', '/health');
    }
    return result;
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
