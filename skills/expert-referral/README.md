# 🌊 China Top Doctor Referral — Specialist booking via OceanBus Yellow Pages

**Top-tier hospital specialist referral service. Publish once, discoverable by any OceanBus agent.**

[![ClawHub](https://img.shields.io/badge/ClawHub-china--top--doctor--referral-blue)](https://clawhub.ai/skills/china-top-doctor-referral)
[![OceanBus](https://img.shields.io/badge/OceanBus-Yellow%20Pages-1a3a5c)](https://www.npmjs.com/package/oceanbus)
[![license](https://img.shields.io/badge/license-MIT--0-green)](LICENSE)

---

## What it does

228 chief physicians and associate chief physicians from China's top hospitals — Peking Union, Fudan-affiliated, SJTU-affiliated, and more — available for outpatient booking at private clinics (United Family, Yide, etc.) in Beijing and Shanghai.

Search by department, disease keyword, or symptom. Get structured results ready for display or further processing.

## Two ways to use

### 1. LLM conversation (traditional)

Install the skill and ask: "北京呼吸科专家"

```bash
openclaw skills install china-top-doctor-referral
```

### 2. OceanBus Yellow Pages service (new)

Register as a discoverable service. Any OceanBus agent can find and query it.

```bash
npm install                          # install OceanBus SDK
node scripts/register.js             # one-time: register + publish to YP
node scripts/serve.js                # long-running: listen for queries
```

Other agents discover and query:

```json
// Search request
{ "query": "心内科" }

// JSON response
{
  "query": "心内科",
  "primary": [
    { "name": "张医生", "title": "主任医师", "practice_hospital": "和睦家", ... }
  ],
  "secondary": [...],
  "total_matches": 15
}
```

## Data

- 228 experts from 3 data sources (Yide Hospital, Shanghai UFH external specialists, UFH Puxi external specialists)
- Search by department, disease, or symptom (70+ symptom→dept mappings)

## Related Projects

- [OceanBus SDK](https://www.npmjs.com/package/oceanbus) — core infrastructure (`npm install oceanbus`)
- [health-checkup-recommender](https://clawhub.ai/skills/health-checkup-recommender) — evidence-based checkup plans
- [Ocean Chat](https://clawhub.ai/skills/ocean-chat) — P2P messaging & Yellow Pages discovery
- [ClawHub OceanBus collection](https://clawhub.ai/skills?search=oceanbus)

## License

MIT-0
