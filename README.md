# 🌊 健康体检推荐 — OceanBus 黄页上的循证体检服务

**个性化体检方案推荐。发布一次，任何 OceanBus Agent 都能搜到你。**

[![ClawHub](https://img.shields.io/badge/ClawHub-health--checkup--recommender-blue)](https://clawhub.ai/skills/health-checkup-recommender)
[![clones](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ryanbihai/health-checkup-recommender/main/clones.json)](https://github.com/ryanbihai/health-checkup-recommender/graphs/traffic)
[![GitHub stars](https://img.shields.io/github/stars/ryanbihai/health-checkup-recommender)](https://github.com/ryanbihai/health-checkup-recommender)
[![OceanBus](https://img.shields.io/badge/OceanBus-Yellow%20Pages-1a3a5c)](https://www.npmjs.com/package/oceanbus)
[![license](https://img.shields.io/badge/license-MIT--0-green)](LICENSE)

---

## 循证医学支撑

所有风险评估和体检项目推荐，均基于权威医学数据：

- **国家卫建委《成人健康体检项目推荐指引（2025 版）》** — 体检项目框架
- **BMJ / JAMA 顶刊文献** — 中国人群慢性病风险模型（2021-2025）
- **国家癌症中心** — 恶性肿瘤风险排序（2022 年中国癌症报告）

每一项推荐都标明出处，不做过度的无根据推销。

## 两种用法

### 1. LLM 对话（传统方式）

安装 skill，对你的 AI 说"我想做体检"：

```bash
openclaw skills install health-checkup-recommender
```

### 2. OceanBus 黄页服务（新）

注册为可发现服务，任何 OceanBus Agent 都能发来体检请求。

```bash
npm install                          # 安装 OceanBus SDK + qrcode
node scripts/register.js             # 一次性：注册 OceanBus + 发布到黄页
node scripts/serve.js                # 长期运行：监听体检推荐请求
```

其他 Agent 发送患者信息，收到完整推荐方案：

```json
// 请求
{ "age": 45, "gender": "male", "symptoms": ["胸闷", "胃痛"], "consent": false }

// 回复
{
  "riskAssessment": [{ "disease": "肝癌", "explanation": "..." }],
  "recommendations": [{ "id": "HaoLa01", "name": "一般检查", "price": 11 }],
  "totalPrice": 424
}
```

`"consent": true` 时可自动生成预约二维码（base64 data URI）。

## 相关项目

- [OceanBus SDK](https://www.npmjs.com/package/oceanbus) — 核心基础设施（`npm install oceanbus`）
- [china-top-doctor-referral](https://clawhub.ai/skills/china-top-doctor-referral) — 三甲专家推荐服务
- [Ocean Chat](https://clawhub.ai/skills/ocean-chat) — P2P 消息 + 黄页发现
- [ClawHub OceanBus 集合](https://clawhub.ai/skills?search=oceanbus)

## License

MIT-0
