---
name: health-checkup-recommender
description: AI 智能健康体检推荐服务。严格依据《国家卫建委成人体检指引（2025版）》、BMJ及国家癌症中心最新流行病学数据，为您提供具有权威循证医学支撑的个性化体检方案。覆盖全国220城市数百家体检机构预约。二维码预约需用户明确同意。
homepage: https://www.ihaola.com.cn
metadata:
  category: utility
  api_base: https://pe.ihaola.com.cn
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
      - node: '>=18.0.0'
    install:
      - npm ci
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

1. **不读取本地敏感文件**：所有配置均通过标准环境变量（`NODE_ENV`）控制，无需读取本地配置文件
2. **不自动发送二维码**：必须询问用户同意后才能发送
3. **数据脱敏与传输限制**：
   - **仅一个脚本发起网络请求**：`scripts/sync_items.js`（项目同步）
   - **传输内容**：`{ itemIds: ["HaoLa01", "HaoLa12", "HaoLa57"] }` — 仅脱敏的体检项目 ID
   - **绝不传输**：姓名、手机号、身份证号或任何 PII 数据
   - **二维码内容**：仅含 `welfareid`/`ruleid` 两个脱敏预约码，无任何个人信息
   - 详细说明见 `SECURITY_AUDIT.md`

### 网络请求透明度声明 (sync_items.js)

为便于安全审计，在此完整公开本技能唯一网络请求（`scripts/sync_items.js`）的实现细节。本技能**绝不**读取任何本地敏感文件（如 `.env`），也**绝不**在请求体或 Header 中夹带任何个人身份信息（PII）。

**HTTP 请求示例：**
```http
POST https://pe.ihaola.com.cn/skill/api/recommend/addpack
Content-Type: application/json

{
  "itemIds": ["HaoLa01", "HaoLa12", "HaoLa57"]
}
```
*说明：请求体仅包含脱敏的体检项目内部编号数组，无任何用户标识、会话 Token 或自由文本。*

**HTTP 响应示例：**
```json
{
  "code": 0,
  "data": {
    "welfareid": "c99a14f6e0",
    "ruleid": "a0828f3e01"
  }
}
```
*说明：服务器仅返回脱敏的业务关联 ID，用于后续生成本地二维码。二维码同样不含 PII，用户扫码后需在官网自行填写信息。*

4. **脚本行为一览**：verify_items.js、calculate_prices.js、check_conflicts.js 为纯本地处理，generate_qr.js 仅生成本地图片
5. **运行时依赖**：需在环境中执行 `npm ci`（已在 `_meta.json` 和 metadata 的 `install` 中声明，使用 `npm ci` 基于 `package-lock.json` 安装确保依赖树的一致性和安全性）

---

## 核心原则

### 执行流程原则（必须全部执行）

1. **信息收集**：向用户询问年龄、性别、症状、家族史等必要信息
2. **风险评估**：查询 `reference/risk_logic_table.json`
3. **症状匹配**：查询 `reference/symptom_mapping.json`（含同义词映射）
4. **项目验证（强制）**：调用 `node scripts/verify_items.js [推荐项目]`
5. **价格计算（强制）**：调用 `node scripts/calculate_prices.js [推荐项目]`
6. **输出推荐**：使用 `PROMPTS.md` 中的话术模板输出
7. **获取套餐脱敏welfareid和ruleid**：调用 `node scripts/sync_items.js [推荐项目]`
8. **二维码生成（强烈推荐）**：`node scripts/generate_qr.js --consent=true output.png [welfareid] [ruleid]`

### 数据查询原则

- **项目清单**：查询 `reference/checkup_items.json`（唯一可信来源）
- **循证依据**：查询 `reference/evidence_mappings_2025.json`
- **禁止编造**：只能推荐数据库中存在的项目

### 重要规则

| 规则 | 说明 |
|------|------|
| **600元 最低消费** | 由于合作体检机构不接低于 600 元的订单，不足时需向用户说明原因并补充推荐项目 |
| **HaoLa01 必选** | 体检基线数据（身高/体重/血压等），每个套餐必须包含 |
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

#### 2c. 风险解读（必需）

```bash
# 结合用户信息查询 reference/evidence_mappings_2025.json
# 从 personal_explanations 中选择匹配的深度解读
# 输出具备说服力的专业健康咨询建议
```

#### 2d. 项目验证（强制）

```bash
node scripts/verify_items.js [推荐项目...]

# 检查返回码：0=全部有效 1=有无效项目→修正
```

#### 2e. 价格计算（强制）

```bash
node scripts/calculate_prices.js [推荐项目...]

# 输出：项目明细、自动去重、总价
```

#### 2f. 获取套餐脱敏welfareid和ruleid（生成二维码的前置条件，不可缺！）

```bash
node scripts/sync_items.js [推荐项目...]

# 输出：welfareid、ruleid 两个脱敏预约码
```

#### 2g. 二维码生成（强烈推荐）

```bash
# 优先使用智能降级脚本
node scripts/generate_qr.js --consent=true output.png [welfareid] [ruleid]

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
  SECURITY_AUDIT.md          # 安全审核与隐私说明
  reference/
    checkup_items.json        # 唯一可信来源
    symptom_mapping.json
    evidence_mappings_2025.json
    risk_logic_table.json
    booking_info.md
  scripts/
    verify_items.js            # 项目验证（强制）
    calculate_prices.js       # 价格计算（强制）
    sync_items.js             # 唯一网络请求脚本
    check_conflicts.js        # 冲突检测
    generate_qr.js           # 本地二维码生成
    validate_skill.js          # 安全验证脚本
  config/
    api.js                   # API 端点配置
```

---

## 版本更新

| 日期 | 版本 | 更新 |
|------|------|------|
| 2026-04-07 | 4.2.3 | 修复 generate_qr.py 中的 DEBUG_MODE 文件检查，统一使用 NODE_ENV |
| 2026-04-07 | 4.2.2 | 增强 SECURITY_AUDIT.md 脚本行为矩阵；添加 .gitignore；更新 SKILL.md 网络行为说明 |
| 2026-04-07 | 4.2.1 | 修复安全扫描告警：移除 config/api.js 中对 .env 文件检查，统一使用 NODE_ENV；调整 validate_skill.js 检查列表 |
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
node scripts/calculate_prices.js HaoLa12 HaoLa57

# 项目验证（强制）
node scripts/verify_items.js HaoLa12 HaoLa57

# 智能二维码（推荐）
node scripts/generate_qr.js --consent=true output.png

# 安全验证（发布前检查）
node scripts/validate_skill.js
```

---

**详细话术模板请查看** **`PROMPTS.md`**
