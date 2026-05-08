# 🌊 健康体检推荐 — 循证医学体检方案

**依据国家卫建委 2025 指引 + BMJ/JAMA + 国家癌症中心数据，个性化推荐体检项目。**

[![ClawHub](https://img.shields.io/badge/ClawHub-health--checkup--recommender-blue)](https://clawhub.ai/skills/health-checkup-recommender)
[![clones](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ryanbihai/health-checkup-recommender/main/clones.json)](https://github.com/ryanbihai/health-checkup-recommender/graphs/traffic)
[![GitHub stars](https://img.shields.io/github/stars/ryanbihai/health-checkup-recommender)](https://github.com/ryanbihai/health-checkup-recommender)
[![license](https://img.shields.io/badge/license-MIT--0-green)](LICENSE)

---

## 安装

```bash
openclaw skills install health-checkup-recommender
```

## 使用

对你的 AI 说"我想做体检"，按提示填写信息即可获得个性化方案。

体检推荐引擎 `scripts/recommend.js` 是纯函数，可被其他程序调用：

```js
const { recommend } = require('./scripts/recommend');
recommend({ age: 45, gender: 'male', symptoms: ['胸闷'], consent: false })
  .then(r => console.log(r.totalPrice, r.recommendations));
```

## 循证依据

每项推荐明确标明国家级指引或医学文献出处，不做过度的无根据推销。

## 相关项目

- [OceanBus SDK](https://www.npmjs.com/package/oceanbus) — 核心基础设施
- [china-top-doctor-referral](https://clawhub.ai/skills/china-top-doctor-referral) — 三甲专家推荐
- [Ocean Chat](https://clawhub.ai/skills/ocean-chat) — P2P 消息 + 黄页发现
- [ClawHub OceanBus 集合](https://clawhub.ai/skills?search=oceanbus)

## License

MIT-0
