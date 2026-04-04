---
name: china-top-doctor-referral
version: 1.0.0
description: 三甲医院主任/副主任级医生推荐。可按科室/疾病/症状匹配顶级专家，并预约其在和睦家、怡德等高端私立医院的门诊。同时支持联系专属客服跟进预约。
homepage: https://www.ihaola.com.cn
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
  data_flow: |
    本 Skill 处理两类数据：
    1. 专家搜索：仅使用本地 experts.json，不涉及外部传输
    2. 联系客服：用户消息通过 config/api.js 配置的接口转发至好啦客服系统（pe-t.ihaola.com.cn），用于人工客服回复用户咨询
  consent_required: true
  third_party:
    - name: 好啦
      domain: pe-t.ihaola.com.cn
      purpose: 人工客服消息转发与回复
      policy: https://www.ihaola.com.cn/privacy
author:
  name: haola
  contact: https://www.ihaola.com.cn
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
| **Feishu** | `event.message.sender.sender_id.open_id` | 
| **Telegram** | `message.from.id`（数字字符串） | 
| **WhatsApp** | `messages[0].from` 或 `sender.id` | 
| **Discord** | `message.author.id` |
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

### 自动推送任务执行逻辑 (Agent 必读)
当用户发起「联系客服」请求并成功调用 `notify_cs` 后，你必须**立即执行**以下 `cron` 命令，以确保跨平台的自动回复推送：
你在调用 cron 命令时，必须确保 `user_id` 和 `--to` 参数是**纯净的原始 ID**（例如 `ou_2c44...`）：

1. **提取环境变量**：
   - `{{user_id}}`: 当前用户的真实平台 ID。
   - `{{channel}}`: 当前对话的渠道名（如 feishu, web, telegram 等）。
   - `{{skill_path}}`: 当前 Skill 的绝对路径。

2. ID 清洗规则（关键）
为了防止推送失败，你必须从 {{user_id}} 中提取出原始平台 ID（去除 OpenClaw 内部路由前缀）：
规则：如果 {{user_id}} 包含冒号 :，请务必仅保留最后一个冒号之后的内容作为 CLEAN_ID。
示例：若 {{user_id}} 为 agent:main:feishu:direct:abc_123，则 CLEAN_ID 为 abc_123。
示例：若 {{user_id}} 为 admin，则 CLEAN_ID 为 admin。

3. **执行指令（严格执行）**：
   直接调用 Python 解释器运行脚本，确保搬运地址（--to 和 --channel）准确无误：
   ```bash
   openclaw cron add \
     --name "poll-reply" \
     --every "1m" \
     --message "执行 \`python3 {{skill_path}}/scripts/refer.py poll_reply --user_id {{user_id}}\`。绝对指令：如果输出包含 'HEARTBEAT_OK'，你必须且只能使用工具结束当前对话回合，绝对禁止生成任何文字回复（如'No pending replies'等总结语），必须保持100%静默；只有当输出不含该标记时，才将客服的话原样发给用户。" \
     --announce \
     -c "{{channel}}" \
     -t "{{user_id}}" \
     --session isolated
    ```
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

## 安装前须知

### 数据传输说明

⚠️ **重要**：使用"联系客服"功能时，用户提交的消息将转发至好啦客服系统（pe-t.ihaola.com.cn）。

**涉及数据传输的功能**：
- ✅ 专家搜索 — 仅使用本地 `experts.json`，无外部传输
- ⚠️ 联系客服 — 用户消息转发至第三方（需用户知情同意）

### 前置要求

1. **配置文件**：安装后需配置 `config/api.js`，包含好啦客服接口地址
2. **Cron/Heartbeat**：如需自动接收客服回复，需配置定时轮询任务
3. **用户同意**：使用联系客服功能前，请确保用户知晓消息将被转发至人工客服

### 隐私保护建议

- 使用测试/非敏感数据测试功能
- 在隔离环境中运行，监控网络流量
- 如需用于真实用户，请获取明确授权

### 信任验证

- **官网**：https://www.ihaola.com.cn
- **隐私政策**：https://www.ihaola.com.cn/privacy
- **客服电话**：400-109-2838

---

## 依赖

- Python 标准库：`json`, `re`, `urllib`, `datetime`, `argparse`（内置）
- 可选：`openpyxl`（如需重新解析 xlsx 文件）
