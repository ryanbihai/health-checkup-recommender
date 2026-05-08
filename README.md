# 🌊 Health Checkup Recommender — Evidence-based checkup plans via OceanBus Yellow Pages

**Personalized health screening recommendations. Publish once, discoverable by any OceanBus agent.**

[![ClawHub](https://img.shields.io/badge/ClawHub-health--checkup--recommender-blue)](https://clawhub.ai/skills/health-checkup-recommender)
[![GitHub stars](https://img.shields.io/github/stars/ryanbihai/health-checkup-recommender)](https://github.com/ryanbihai/health-checkup-recommender)
[![OceanBus](https://img.shields.io/badge/OceanBus-Yellow%20Pages-1a3a5c)](https://www.npmjs.com/package/oceanbus)
[![license](https://img.shields.io/badge/license-MIT--0-green)](LICENSE)

---

## Evidence-Based Recommendations

All risk assessments and checkup item recommendations are grounded in:

- **National Health Commission 2025 Guidelines** — official checkup item framework
- **BMJ / JAMA** — chronic disease risk models from large-scale Chinese population studies (2021-2025)
- **National Cancer Center** — malignant tumor risk ranking from the 2022 China Cancer Report

Every recommendation carries a clear citation. No unfounded upselling.

## Two ways to use

### 1. LLM conversation (traditional)

Install the skill and say "我想做体检":

```bash
openclaw skills install health-checkup-recommender
```

### 2. OceanBus Yellow Pages service (new)

Register as a discoverable service. Any OceanBus agent can query it with a patient profile.

```bash
npm install                          # install OceanBus SDK + qrcode
node scripts/register.js             # one-time: register + publish to YP
node scripts/serve.js                # long-running: listen for checkup requests
```

Other agents send a patient profile and get a full recommendation:

```json
// Request
{
  "age": 45,
  "gender": "male",
  "symptoms": ["胸闷", "胃痛"],
  "familyHistory": { "cardiovascular": true },
  "consent": false
}

// Response
{
  "riskAssessment": [
    { "disease": "肝癌", "explanation": "..." }
  ],
  "recommendations": [
    { "id": "HaoLa01", "name": "一般检查", "price": 11 }
  ],
  "totalPrice": 424,
  "qrDataUri": null
}
```

Set `"consent": true` to generate a QR code for instant booking on the partner platform.

## Related Projects

- [OceanBus SDK](https://www.npmjs.com/package/oceanbus) — core infrastructure (`npm install oceanbus`)
- [china-top-doctor-referral](https://clawhub.ai/skills/china-top-doctor-referral) — specialist booking service
- [Ocean Chat](https://clawhub.ai/skills/ocean-chat) — P2P messaging & Yellow Pages discovery
- [ClawHub OceanBus collection](https://clawhub.ai/skills?search=oceanbus)

## License

MIT-0
