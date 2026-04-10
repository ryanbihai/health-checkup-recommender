---
name: china-top-doctor-referral
version: 1.4.0
description: 面向高端医疗险客户，推荐和预约（北京）协和医院、北大系、阜外医院、安贞医院、中国医学科学院肿瘤医院；（上海）复旦华山/中山/儿科/肿瘤/眼耳鼻喉医院等顶级三甲医院主任/副主任专家。可按科室/疾病/症状匹配顶级专家，并预约其在和睦家、怡德等高端私立医院的门诊。专属客服跟进协助预约。
homepage: https://www.ihaola.com.cn
metadata:
  category: utility
  api_base: https://pe-t.ihaola.com.cn
  capabilities:
    - api
    - heartbeat
  requires:
    config_paths:
      - config/api.js
  permissions:
    network:
      - https://pe-t.ihaola.com.cn
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

## 触发词与系统事件

- **用户对话触发**：专家推荐, 预约专家, 挂号, 看哪个医生, 找哪个专家, 推荐医生, 想看, 要挂号, 主任, 副主任, 三甲医生, 联系客服, 客服
- **系统事件触发**：当接收到 `type: heartbeat` 的后台静默系统事件时，你必须根据用户全局工作区中配置的轮询指令，主动执行检查任务。

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
      refer.py notify_cs --user_id "真实用户ID" --message "用户的消息" --channel "feishu" --consent=true
           ↓
      消息持久化到 pending_ctx.json
           ↓
      heartbeat 定期调用 refer.py poll_reply（需 Agent 引导用户检查或配置 HEARTBEAT.md）
           ↓
      外部 API 返回客服回复 → 推送用户
```

### ⚠️ 关键：user_id 必须从上下文提取

**绝对禁止自行杜撰 user_id！** 必须从当前对话上下文中获取真实用户身份：

| 渠道           | user_id 字段                              | 示例                |
| ------------ | ---------------------------------------- | ----------------- |
| **Feishu**   | `event.message.sender.sender_id.open_id` | <br />            |
| **Telegram** | `message.from.id`（数字字符串）                 | <br />            |
| **WhatsApp** | `messages[0].from` 或 `sender.id`         | <br />            |
| **Discord**  | `message.author.id`                      | <br />            |
| **Webchat**  | 使用当前会话的 session_key                     | `agent:main:main` |

**提取优先级**：Feishu open_id > Telegram id > 其他渠道用户标识 > session_key

### 使用方式

用户对自己的机器人说：

> **联系客服 我想预约XXX医生，45岁**

**正确调用方式（必须用 exec 工具）：**

```bash
# ⚠️ 注意：必须传入 --user_id 和 --consent=true，不能省略或杜撰
cd <skill目录>/scripts
python3 refer.py notify_cs \
  --user_id "从上下文获取的真实用户身份" \
  --message "用户的消息内容" \
  --channel "{{channel}}" \
  --consent=true
```

### 自动推送任务执行逻辑 (Agent 必读)

当用户发起「联系客服」请求时，**你必须遵循以下安全与隐私规范：**

**⚠️ 隐私与权限警告**：
1. **未经用户明确授权前，绝对禁止**你私自去读取或修改用户的系统全局配置文件（如 `~/.openclaw/workspace/HEARTBEAT.md` 或 `~/.openclaw/openclaw.json`）。
2. 在调用 `notify_cs` 前，**必须先向用户请求明确同意**。

#### 1. 征求用户同意
在执行任何脚本前，你必须向用户输出以下询问：
> “发送消息给客服需要将您的用户标识和消息内容发送至第三方服务器 (pe-t.ihaola.com.cn)，请问您是否同意？”

只有在用户明确回复“同意”后，才能继续下一步。

#### 2. 发送请求并引导用户配置
在获得同意并成功调用 `notify_cs` 后，你**不需要**创建任何后台任务，也**不准去检查配置状态**。

请直接向用户输出以下文本，将配置控制权完全交给用户：

> ✅ 您的请求已成功转达给好啦客服！由于系统的隐私保护限制，我目前无法在后台一直帮您盯着客服的回复。
> 💡 **想让客服回复后自动通知您？** 您可以开启系统的「自动消息提醒（Heartbeat）」功能。配置一次后，有新消息就会立刻推送到这里。
> 
> 👉 **【需要我帮您直接配置并开启吗？请回复“同意”】**

#### 3. 用户同意配置后的协助流程

如果用户明确回复“同意”或“需要”，你将被授权**代为执行**以下配置步骤（注意：必须在获得用户明确同意后，才能操作全局文件）：

1. **集成轮询任务**：读取本 Skill 目录下的 `HEARTBEAT.md` 内容，并使用文件编辑工具将其追加到用户的全局工作区文件（`~/.openclaw/workspace/HEARTBEAT.md`，如文件不存在则创建）中。
2. **配置心跳频率**：读取并修改系统的配置文件 `~/.openclaw/openclaw.json`，确保在 `agents.defaults` 节点下配置心跳的触发频率（例如每 2 分钟）：
   ```json
   "heartbeat": {
     "every": "2m",
     "target": "last"
   }
   ```
   *(注：`target: "last"` 必须保留，它确保 Agent 能准确知道消息应该推送到哪个群组或私聊窗口。)*

3. **启用心跳服务**：使用执行工具在终端运行 `openclaw system heartbeat enable`。

配置完成后，回复用户：“✅ 已为您成功配置并开启了自动消息提醒功能，客服回复后将第一时间通知您。”

### 技术实现

1. 提取真实 user_id → 调用 `refer.py notify_cs --user_id "真实ID" --message "用户消息" --channel "渠道" --consent=true`
2. 消息持久化到 `pending_ctx.json`（存储单用户的轮询上下文）
3. 依赖 全局心跳定期调用 `refer.py poll_reply`
4. 脚本输出 `HEARTBEAT_OK` 时触发静默，输出真实内容时通过机器人主动推送。

### 配置

`config/api.js` 中配置 `baseUrl` 和 API 路径，系统自动解析。

### 接口说明

| 接口   | 方法   | 字段                    | 说明                              |
| ---- | ---- | --------------------- | ------------------------------- |
| 发消息  | POST | `user_id`, `question` | 发送用户消息                          |
| 轮询回复 | GET  | `user_id`             | 返回 `{"data": {"reply": "..."}}` |

### 联系信息

- **电话**：400-109-2838
- **微信公众号**：好啦

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

# 发送客服消息（⚠️ --user_id 和 --consent=true 必填）
python3 refer.py notify_cs --user_id "<真实用户ID>" --message "<消息内容>" --channel "<渠道>" --consent=true

# 轮询客服回复（供 heartbeat 调用）
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
2. **Heartbeat**：如需自动接收客服回复，需配置定时轮询任务
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
