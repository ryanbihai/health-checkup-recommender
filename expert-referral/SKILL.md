---
name: china-top-doctor-referral
version: 1.0.0
description: 三甲医院主任/副主任级医生推荐。可按科室/疾病/症状匹配顶级专家，并预约其在和睦家、怡德等高端私立医院的门诊。同时支持联系专属客服跟进预约。
metadata:
  category: utility
  api_base: https://pe-t.ihaola.com.cn
capabilities:
  - api
  - cron
requires:
  config_paths:
    - config/api.js
  runtime_deps:
    - python: openpyxl
  tools:
    - cron
privacy:
  data_flow: "专家数据来自本地 reference/experts.json；客服消息通过 config/api.js 中的接口中转"
author:
  name: haola
license: MIT
---

# Top Doctor Referral

## 核心价值

**推荐三甲医院主任/副主任级别的医生，让用户预约到顶级专家**

### 专家来源
- 北京协和医院、北大系、阜外医院、安贞医院、中国医学科学院肿瘤医院等
- 复旦华山/中山/儿科/肿瘤/眼耳鼻喉医院等
- 交大附属瑞金/新华/胸科医院、上海儿童医学中心等
- 专家出诊渠道：和睦家医院、怡德医院等高端私立机构

### 数据规模
整合三个 Excel 数据源（`reference/experts.json`，共 228 位专家）：
1. 怡德医院专家信息列表 — 北京怡德医院出诊专家
2. 上海和睦家外院专家合作列表
3. 和睦家浦西外院专家合作列表

## 触发词

**专家推荐, 预约专家, 挂号, 看哪个医生, 找哪个专家, 推荐医生, 想看, 要挂号, 主任, 副主任, 三甲医生, 联系客服, 客服**

---

## 功能一：专家推荐

### 核心逻辑
- **重点展示**：专家的职称（三甲医院主任/副主任）、原单位背景、出诊时间
- **出诊渠道**：和睦家、怡德等高端私立医院（提及即可，作为预约通道）

### 使用方式
直接描述需求，例如：
- "我想预约呼吸科专家"
- "45岁女性乳腺结节，北京推荐谁"
- "肾内科专家有哪些"

### 输出格式
```
✅ **可直接预约的专家**

【城市·科室】姓名 | 职称（三甲主任/副主任）| 出诊：和睦家/怡德 | 时间 | 诊费
擅长：...
原单位：XXX医院

📋 **其他专家（供参考）**
【城市·科室】姓名 | 职称 | 原单位
擅长：...
```

---

## 功能二：联系客服

### 业务流程
```
用户 → 「联系客服 XXX」
           ↓
      提取真实 user_id（见下方说明）
           ↓
      refer.py notify_cs --user_id "真实用户ID" --message "用户的消息"
           ↓
      消息持久化到 pending_ctx.json
           ↓
      cron/heartbeat 定期调用 refer.py poll_reply
           ↓
      外部 API 返回客服回复 → 推送用户
```

### ⚠️ 关键：user_id 必须从上下文提取

**绝对禁止自行杜撰 user_id！** 必须从当前对话上下文中获取真实用户身份：

| 渠道 | user_id 字段 | 示例 |
|------|-------------|------|
| **Feishu** | `event.message.sender.sender_id.open_id` | `ou_c0fffc6e92308bfe031b00ffa7083d9b` |
| **Telegram** | `message.from.id`（数字字符串） | `123456789` |
| **WhatsApp** | `messages[0].from` 或 `sender.id` | `15551234567` |
| **Discord** | `message.author.id` | `987654321` |
| **Webchat** | 使用当前会话的 session_key | `agent:main:main` |

**提取优先级**：Feishu open_id > Telegram id > 其他渠道用户标识 > session_key

### 使用方式
用户对自己的机器人说：
> **联系客服 我想预约XXX医生，45岁**

**正确调用方式（必须用 exec 工具）：**

```bash
# ⚠️ 注意：必须传入 --user_id，不能省略或杜撰
cd <skill目录>/scripts
python3 refer.py notify_cs \
  --user_id "从上下文获取的真实用户身份" \
  --message "用户的消息内容"
```

### 自动轮询配置（必须）

**⚠️ 本功能依赖 cron 任务持续轮询。每次联系客服后，必须执行以下步骤：**

#### 第一步：检查是否已有轮询任务
执行 `cron list`（工具调用），检查是否存在 `expert-referral-poll` 相关任务。

#### 第二步：如无，则创建 cron 任务
如果不存在，使用 `cron add`（工具调用）创建轮询任务：

```
名称：expert-referral-poll
执行频率：每 2 分钟一次（everyMs: 120000）
sessionTarget：isolated（独立会话，不影响主对话）
delivery：announce（将结果推送给用户）
payload.kind：agentTurn
payload.message：执行以下操作——先 cd 到 ~/.openclaw/skills/expert-referral/scripts，然后运行 python3 refer.py poll_reply 检查客服回复。如有回复，将回复内容整理后通过当前渠道推送给用户。如无回复，保持沉默，不要输出任何内容。
```

**⚠️ 注意**：
- `sessionTarget` 必须为 `isolated`，禁止使用 `main` 或 `current`（会干扰正常对话）
- `delivery.mode` 必须为 `announce`，这样 cron 执行完才会推送结果

### 技术实现
1. 提取真实 user_id → 调用 `refer.py notify_cs --user_id "真实ID" --message "用户消息"`
2. 消息持久化到 `pending_ctx.json`（存储 user_id 和咨询上下文）
3. 依赖 cron/heartbeat 任务定期调用 `refer.py poll_reply`
4. 有回复则通过机器人主动推送

### 配置
`config/api.js` 中配置 `baseUrl` 和 API 路径，系统自动解析。

### 接口说明
| 接口 | 方法 | 字段 | 说明 |
|------|------|------|------|
| 发消息 | POST | `user_id`, `question` | 发送用户消息 |
| 轮询回复 | GET | `user_id` | 返回 `{"data": {"reply": "..."}}` |

### 联系信息
- **电话**：400-109-2838
- **微信公众号**：好啦
  ![好啦公众号](images/haola_qr.jpg)

---

## 文件结构

```
expert-referral/
├── SKILL.md              # 本文件
├── HEARTBEAT.md          # 自动轮询任务配置
├── reference/
│   └── experts.json      # 专家数据库（228位专家）
├── scripts/
│   └── refer.py          # 推荐引擎 + 客服接口
├── config/
│   └── api.js            # 接口配置
└── images/
    └── haola_qr.jpg      # 公众号二维码
```

---

## scripts/refer.py 命令行接口

```bash
# 搜索专家
python3 refer.py search <关键词>

# 发送客服消息（⚠️ --user_id 必填）
python3 refer.py notify_cs --user_id "<真实用户ID>" --message "<消息内容>"

# 轮询客服回复（供 cron/heartbeat 调用）
python3 refer.py poll_reply
```

---

## 依赖

- Python 标准库：`json`, `re`, `urllib`, `datetime`, `argparse`（内置）
- 可选：`openpyxl`（如需重新解析 xlsx 文件）
