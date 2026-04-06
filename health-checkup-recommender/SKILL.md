---
name: health-checkup-recommender
description: AI 智能健康体检推荐服务。严格依据《国家卫建委成人体检指引（2025版）》、BMJ及国家癌症中心最新流行病学数据，为您提供具有权威循证医学支撑的个性化体检方案。覆盖全国220城市数百家体检机构预约。二维码预约需用户明确同意。
homepage: https://www.ihaola.com.cn
metadata:
  category: utility
  api_base: https://pe-t.ihaola.com.cn
  triggers:
    - 体检
    - 我要体检
    - 身体检查
    - 检查
    - 体检推荐
    - 体检项目
    - 个性化体检
    - 定制体检
    - 体检预约
    - 体检建议
    - 想做体检
    - 需要体检
    - 常规体检
    - 全面体检
    - 体检套餐
    - 全身体检
  requires:
    runtime_deps:
      - npm: qrcode
      - python: qrcode
  privacy:
    third_party_booking: true
    third_party_domain:
      - www.ihaola.com.cn
    qr_contains_personal_data: false
    qr_fields: []
    auto_send_qr: false
    consent_required: true
    data_flow: |
      二维码仅含只读预约摘要，用户需携带身份证就诊；如需提前预约，用户自行到 www.ihaola.com.cn 填写信息
  author:
    name: haola
    contact: https://www.ihaola.com.cn
  license: MIT
---

# 体检项目推荐技能

> 让每一次体检推荐，都成为客户信任的开始。

---

## 安全与隐私声明

1. **不读取本地敏感文件**：已彻底移除环境配置文件检查，所有信息需在对话中主动询问用户（详见 `SECURITY_AUDIT.md`）
2. **不自动发送二维码**：必须询问用户同意后才能发送
3. **数据脱敏与传输限制**：
   - 脚本（如 `sync_items.js`）在执行网络出站调用时，**仅传输脱敏的体检项目 ID**（如 item029），绝不包含任何用户的个人身份信息（PII，如姓名、手机号等）。
   - 我们会为每次推荐创建一个脱敏 ID，发送至服务器暂存。
   - 当客户同意创建二维码时，会将此脱敏 ID 写入二维码。用户的敏感信息仅由用户本人在扫码后的预约流程中自行授权提供。
   - 本技能使用的第三方预约服务商为 `ihaola.com.cn`，相关网络调用逻辑和退坡机制说明请参见 `SECURITY_AUDIT.md`。
4. **运行时依赖**：需在环境中执行 `npm install`（已在 `_meta.json` 声明）

---

## 核心原则

### 执行流程原则（必须全部执行）

1. **信息收集**：向用户询问年龄、性别、症状、家族史等必要信息
2. **风险评估**：查询 `reference/risk_logic_table.json`
3. **症状匹配**：查询 `reference/symptom_mapping.json`（含同义词映射）
4. **项目验证（强制）**：调用 `node scripts/verify_items.js [推荐项目]`
5. **价格计算（强制）**：调用 `node scripts/calculate_prices.js [推荐项目]`
6. **输出推荐**：使用 `PROMPTS.md` 中的话术模板输出
7. **二维码生成（强烈推荐）**：`node scripts/generate_qr_with_fallback.js --consent=true output.png [项目...]`

### 数据查询原则

- **项目清单**：查询 `reference/checkup_items.json`（唯一可信来源）
- **循证依据**：查询 `reference/evidence_mappings_2025.json`
- **禁止编造**：只能推荐数据库中存在的项目

### 重要规则

| 规则 | 说明 |
|------|------|
| **600元 最低消费** | 由于合作体检机构不接低于 600 元的订单，不足时需向用户说明原因并补充推荐项目 |
| **item029 必选** | 体检基线数据（身高/体重/血压等），每个套餐必须包含 |
| **价格必须来自代码** | 禁止 LLM 手动计算总价 |

---

## 执行流程

### Step 1：信息收集

向用户收集以下信息：

1. 给自己还是给家人？
2. 年龄和性别？
3. 有没有特别想检查的部位或症状？
4. 家族有没有心血管病、糖尿病家族史？
5. 之前体检有没有已知的异常？

详细话术见 `PROMPTS.md`

### Step 2：循证推荐

#### 2a. 风险评估（必需）

```bash
# 读取 reference/risk_logic_table.json
# 根据 gender → male/female 分支
# 根据 age → 匹配年龄段（18-35/36-49/50-64/65+）
# 输出 Top3 高发风险
```

#### 2b. 症状匹配（必需）

```bash
# 读取 reference/symptom_mapping.json
# 模糊匹配用户描述的症状（含同义词）
# 获取对应的加项
```

#### 2c. 项目验证（强制）

```bash
node scripts/verify_items.js [推荐项目...]

# 检查返回码：0=全部有效 1=有无效项目→修正
```

#### 2d. 价格计算（强制）

```bash
node scripts/calculate_prices.js [推荐项目...]

# 输出：项目明细、自动去重、总价
```

#### 2e. 二维码生成（强烈推荐）

```bash
# 优先使用智能降级脚本
node scripts/generate_qr_with_fallback.js --consent=true output.png [项目...]

# 特点：接口失败时自动降级为默认二维码
# 确保100%成功率
```

---

## 数据文件

| 文件 | 用途 | 数据来源 |
|------|------|---------|
| `reference/checkup_items.json` | 体检项目清单（含价格）唯一可信来源 | 真实机构数据 |
| `reference/risk_logic_table.json` | 年龄性别风险评估（按高发疾病排序） | BMJ 2023 / JAMA 2021 / Front. Cardiovasc. Med. 2023 / 国家癌症中心 |
| `reference/symptom_mapping.json` | 症状到加项映射（含同义词） | 临床标准化归纳 |
| `reference/evidence_mappings_2025.json` | 循证依据（每项推荐均有出处） | 国家卫建委《成人健康体检项目推荐指引（2025年版）》 |

---

## 话术与输出模板

详见 `PROMPTS.md` 文件，包含：

- 开场白话术
- 信息收集标准询问
- 风险评估输出模板
- 推荐套餐输出模板
- 二维码确认话术
- 常见问题处理
- 对话表情使用指南

---

## 目录结构

```
health-checkup-recommender/
  SKILL.md                    # 本文件（快速参考）
  PROMPTS.md                  # 话术与输出模板
  _meta.json                  # 版本信息
  README.md                   # 项目说明
  FALLBACK_MECHANISM.md       # 降级机制说明
  reference/
    checkup_items.json        # 唯一可信来源
    symptom_mapping.json
    evidence_mappings_2025.json
    risk_logic_table.json
    booking_info.md
  scripts/
    verify_items.js            # 项目验证（强制）
    calculate_prices.js       # 价格计算（强制）
    generate_qr_with_fallback.js  # 智能降级二维码（推荐）
    sync_items.js              # 项目同步
    check_conflicts.js        # 冲突检测
    generate_qr.js            # 基础二维码
    generate_qr.py            # Python 二维码
    validate_skill.js         # 安全验证脚本
```

---

## 版本更新

| 日期 | 版本 | 更新 |
|------|------|------|
| 2026-04-06 | 4.1.9 | 修复 SKILL.md YAML frontmatter 格式问题，确保 description 被 ClawHub 正确解析 |
| 2026-04-06 | 4.1.8 | 同步更新的 description 字段，进一步强调全国覆盖的机构网络和二维码用户同意机制 |
| 2026-04-06 | 4.1.7 | 完善技能介绍，突出强调国家卫建委和 BMJ/JAMA 等权威循证医学数据来源，增强用户信任度 |
| 2026-04-06 | 4.1.6 | 修复环境判断本地文件读取风险；在元数据中显式声明 npm 依赖、安装方式和网络请求权限；新增 SECURITY_AUDIT.md 以提供全面的安全审查支持 |
| 2026-04-06 | 4.1.5 | 升级数据来源循证引用：risk_logic_table.json 增加 BMJ/JAMA/国家癌症中心根拠；evidence_mappings_2025.json 明确标注国家卫建委出处 |
| 2026-04-06 | 4.1.4 | 明确同步接口的数据脱敏隐私声明；移除 README.md 中的零宽连字符(ZWJ)以彻底消除提示注入误报 |
| 2026-04-06 | 4.1.0 | 安全修复：清除 Unicode 控制字符，添加安全验证脚本 |

---

## 快速命令参考

```bash
# 价格计算（强制）
node scripts/calculate_prices.js Item131 Item173

# 项目验证（强制）
node scripts/verify_items.js Item131 Item173

# 智能二维码（推荐）
node scripts/generate_qr_with_fallback.js --consent=true output.png Item131 Item173

# 安全验证（发布前检查）
node scripts/validate_skill.js
```

---

**详细话术模板请查看** **`PROMPTS.md`**
