***

name health-checkp-recommender
description 健康体检推荐服务。根据年龄/性别/症状/家族史推荐体检项目，循证依据，代码核查确保项目真实。二维码预约需用户明确同意，不自动发送。
**触发词：体检,我要体检,身体检查,检查,体检推荐,体检项目,个性化体检,定制体检,体检预约,体检建议,想做体检,需要体检,常规体检,入职体检,全面体检,体检套餐,全身体检**
reqires
rntime_deps

- npm qrcode
- python qrcode
  privacy
  third_party_booking tre
  third_party_domain www.ihaola.com.cn](http//www.ihaola.com.cn)
  qr_contains_personal_data false
  qr_fields ]
  ato_send_qr false
  consent_reqired tre
  data_flow "二维码仅含只读预约摘要，用户需携带身份证就诊；如需提前预约，用户自行到 www.ihaola.com.cn](http//www.ihaola.com.cn) 填写信息"

***

# 🏥 体检项目推荐技能

 让每一次体检推荐，都成为客户信任的开始。

***

## ⚠️ 安全与隐私声明

. **不读取本地敏感文件**：所有信息需在对话中主动询问用户
. **不自动发送二维码**：必须询问用户同意后才能发送
. **运行时依赖**：需安装 `npm install qrcode` 或 `pip install qrcode`

***

## 🔑 核心原则

### 执行流程原则（必须全部执行）

. **信息收集**：向用户询问年龄、性别、症状、家族史等必要信息
. **风险评估**：查询 `reference/risk_logic_table.json`
. **症状匹配**：查询 `reference/symptom_mapping.json`（含同义词映射）
. **项目验证（强制）**：调用 `node scripts/verify_items.js item 推荐项目]`
. **价格计算（强制）**：调用 `node scripts/calclate_prices.js item 推荐项目]`
. **输出推荐**：使用 `.md` 中的话术模板输出
. **二维码生成（强烈推荐）**：`node scripts/generate_qr_with_fallback.js otpt.png 项目...]`

### 数据查询原则

- **项目清单**：查询 `reference/checkp_items.json`（唯一可信来源）
- **循证依据**：查询 `reference/evidence_mappings_.json`
- **禁止编造**：只能推荐数据库中存在的项目

### 重要规则

| 规则             | 说明                 |
| -------------- | ------------------ |
| **¥ 最低消费**  | 总价不足时自动补充高风险项目     |
| **item 必选** | 每个套餐必须包含常规检查（自动加入） |
| **价格必须来自代码**   | 禁止  手动计算总价      |

***

## 📖 执行流程

### tep ：信息收集

向用户收集以下信息：

. 给自己还是给家人？
. 年龄和性别？
. 有没有特别想检查的部位或症状？
. 家族有没有心血管病、糖尿病家族史？
. 之前体检有没有已知的异常？

详细话术见 `.md`

### tep ：循证推荐

#### a. 风险评估（必需）

```bash
# 读取 reference/risk_logic_table.json
# 根据 gender → male/female 分支
# 根据 age → 匹配年龄段（-/-/-/+）
# 输出 op 高发风险
```

#### b. 症状匹配（必需）

```bash
# 读取 reference/symptom_mapping.json
# 模糊匹配用户描述的症状（含同义词）
# 获取对应的加项
```

#### c. 项目验证（强制）

```bash
node scripts/verify_items.js item 推荐项目...]

# 检查返回码：全部有效  有无效项目→修正
```

#### d. 价格计算（强制）

```bash
node scripts/calclate_prices.js item 推荐项目...]

# 输出：项目明细、自动去重、总价
```

#### e. 二维码生成（强烈推荐）

```bash
# 优先使用智能降级脚本
node scripts/generate_qr_with_fallback.js otpt.png item 项目...]

# 特点：接口失败时自动降级为默认二维码
# 确保%成功率
```

***

## 📁 数据文件

| 文件                                      | 用途                  |
| --------------------------------------- | ------------------- |
| `reference/checkp_items.json`          | 体检项目清单（含价格）⚠️唯一可信来源 |
| `reference/risk_logic_table.json`       | 年龄性别风险评估            |
| `reference/symptom_mapping.json`        | 症状→加项映射（含同义词）       |
| `reference/evidence_mappings_.json` | 循证依据                |

***

## 📝 话术与输出模板

详见 `.md` 文件，包含：

- ✅ 开场白话术
- ✅ 信息收集标准询问
- ✅ 风险评估输出模板
- ✅ 推荐套餐输出模板
- ✅ 二维码确认话术
- ✅ 常见问题处理
- ✅ 对话表情使用指南

***

## 📂 目录结构

```
health-checkp-recommender/
  📄 .md                    # 本文件（快速参考）
  📄 .md                  # 话术与输出模板
  📄 _meta.json                  # 版本信息
  📄 .md                   # 项目说明
  📄 _.md       # 降级机制说明
  📄 reference/
    📄 checkp_items.json        # ⚠️ 唯一可信来源
    📄 symptom_mapping.json
    📄 evidence_mappings_.json
    📄 risk_logic_table.json
    📄 booking_info.md
  📄 scripts/
    📄 verify_items.js            # ✅ 项目验证（强制）
    📄 calclate_prices.js       # ✅ 价格计算（强制）
    📄 generate_qr_with_fallback.js  # ✅ 智能降级二维码（推荐）
    📄 sync_items.js              # 项目同步
    📄 check_conflicts.js        # 冲突检测
    📄 generate_qr.js            # 基础二维码
    📄 generate_qr.py            # ython 二维码
```

***

## 📌 版本更新

| 日期         | 版本    | 更新                                             |
| ---------- | ----- | ---------------------------------------------- |
| -- | .. | **精简重构**：移除重复内容，创建独立 .md，话术模板与核心逻辑分离    |
| -- | .. | **二维码降级机制**：新增 generate_qr_with_fallback.js |
| -- | .. | **价格计算强制化**：新增 calclate_prices.js            |
| -- | .. | **安全加强**：移除 .md 读取权限                       |

***

## 🔗 快速命令参考

```bash
# 价格计算（强制）
node scripts/calclate_prices.js tem tem tem

# 项目验证（强制）
node scripts/verify_items.js tem tem tem

# 智能二维码（推荐）
node scripts/generate_qr_with_fallback.js otpt.png tem tem tem
```

***

**详细话术模板请查看** **`.md`**
