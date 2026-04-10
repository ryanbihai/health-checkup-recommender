---
name: china-top-doctor-referral
version: 1.4.6
description: 面向高端医疗险客户，推荐和预约顶级三甲医院专家。可按科室/疾病匹配专家并预约高端私立门诊。专属客服跟进协助预约。
homepage: https://www.ihaola.com.cn
metadata:
  category: utility
  api_base: https://pe-t.ihaola.com.cn
  capabilities:
    - api
    - cron
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
- **系统事件触发**：为接收客服回复，本系统提供两种触发机制，用户可任选其一：
  1. **独立定时任务 (Cron)**：为每次咨询动态创建 `isolated cron` 任务，获取回复后推送。
  2. **全局心跳轮询 (Heartbeat)**：当接收到 `type: heartbeat` 的系统事件时，根据配置主动执行检查任务。

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
      引导用户选择通知方式 (Isolated Cron 或 全局 Heartbeat)
           ↓
      方案A: Cron 独立进程定期调用 refer.py poll_reply --user_id "真实用户ID"
      方案B: 依赖全局心跳定期调用 refer.py poll_reply (配合 HEARTBEAT.md)
           ↓
      获取到客服回复后 → 推送给用户 (Cron模式使用 openclaw message，Heartbeat模式直接推送)
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

**⚠️ 隐私与系统修改绝对红线**：
1. **未经用户明确且充分的知情授权前，绝对禁止**你将用户的任何标识（user_id）、消息内容等转发至任何第三方服务器。
2. **未经用户明确且充分的知情授权前，绝对禁止**你私自创建持久化的定时任务（Cron）。
3. **未经用户明确且充分的知情授权前，绝对禁止**你私自读取或修改用户的系统全局配置文件（如 `~/.openclaw/workspace/HEARTBEAT.md` 或 `~/.openclaw/openclaw.json`）。

#### 1. 征求全面授权与知情同意
在执行任何脚本、创建任务或修改配置前，你必须向用户发送以下**完整的授权提示**，并等待用户回复：

> ⚠️ **安全与隐私授权请求**
> 为了帮您联系好啦客服并在收到回复时自动通知您，我需要执行以下操作。请问您是否了解并同意？
> 
> 1. **数据传输**：将您的用户标识和咨询内容发送至第三方服务器 (pe-t.ihaola.com.cn)。
> 2. **创建后台任务**：为了自动接收客服回复，需要在您的系统中创建一个独立的定时轮询任务 (Cron)；或者修改您的全局系统配置开启 Heartbeat 心跳轮询。
> 
> 👉 **如果您了解并同意上述操作，请回复“同意”。如果您不同意，我将不会执行任何操作。**

只有在用户明确回复“同意”后，才能继续下一步。

#### 2. 发送请求并引导用户选择通知方式
在获得同意后，调用 `notify_cs` 命令发送消息。发送成功后，向用户提供两种消息接收方式供其选择：

> ✅ 您的请求已成功转达给好啦客服！
> 💡 **请选择您偏好的客服回复自动接收方式：**
>
> **方式一：专属定时任务 (推荐)**
> 仅为本次咨询开启一个独立的定时任务接收回复。回复到达时直接通知您。（回复“1”或“任务”）
> 
> **方式二：全局消息提醒 (Heartbeat)**
> 开启系统的「自动消息提醒」功能，适合长期接收各类系统通知。此操作需要您修改全局 OpenClaw 配置。（回复“2”或“心跳”）
> 
> 👉 **【请选择 1 或 2，我将为您提供详细的配置指令】**

#### 3. 引导用户手动配置（严禁 Agent 代为执行）

**⚠️ 平台安全红线：绝对禁止 Agent 使用执行工具或文件编辑工具代为创建定时任务或修改系统配置文件！**

你只能将具体的配置命令展示给用户，由用户自行决定是否在终端中执行。

**如果用户选择 1（专属定时任务）：**

请向用户回复以下内容（不要自己去执行！）：
> ✅ 已为您成功转达客服。如需开启自动接收回复任务，请在您的系统终端中手动执行以下命令：
> 
> ```bash
> openclaw add cron isolated "python3 <skill绝对路径>/scripts/refer.py poll_reply --user_id '<真实用户ID>'" --every 2m --name "haola_cs_reply_<真实用户ID>"
> ```
> *(注：此命令开启一个独立轮询进程，获取到客服回复后会自动下发纯净消息，随后进程可自动清理)*

**如果用户选择 2（全局消息提醒）：**

请向用户回复以下内容（不要自己去执行！）：
> ✅ 已为您成功转达客服。如需使用全局心跳接收回复，请自行将本 Skill 目录下的 `HEARTBEAT.md` 内容追加到 `~/.openclaw/workspace/HEARTBEAT.md`，并在 `~/.openclaw/openclaw.json` 中配置 heartbeat 频率，最后执行 `openclaw system heartbeat enable`。

### 技术实现

1. 提取真实 user_id → 调用 `refer.py notify_cs --user_id "真实ID" --message "用户消息" --channel "渠道" --consent=true`
2. **Cron 模式**：动态创建 `isolated cron` 定时任务调用 `refer.py poll_reply --user_id "真实ID"`，脚本内部调用 `openclaw message send` 直接向用户下发回复内容。
3. **Heartbeat 模式**：消息持久化，依赖全局心跳定期调用 `refer.py poll_reply`，输出 `HEARTBEAT_OK` 时触发静默，输出真实内容时通过机器人主动推送。

### 配置

`config/api.js` 中配置 `baseUrl` 和 API 路径，系统自动解析。

### 接口说明

| 接口   | 方法   | 字段                    | 说明                              |
| ---- | ---- | --------------------- | ------------------------------- |
| 发消息  | POST | `user_id`, `question` | 发送用户消息                          |
| 轮询回复 | GET  | `user_id`             | 返回 `{"data": {"reply": "..."}}` |

### 联系信息

- **电话**：400-109-2838
- **专属客服微信**：好啦健康管家-张楠<br><img src="images/cs_qr.png" width="200" alt="客服微信二维码">
- **微信公众号**：好啦

---

## 文件结构

```
expert-referral/
├── SKILL1.md             # 本文件
├── HEARTBEAT.md          # 全局心跳任务配置
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

# 轮询客服回复（Cron/Heartbeat 共用）
python3 refer.py poll_reply --user_id "<真实用户ID>"
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
2. **定时任务**：如需自动接收客服回复，需授权 Agent 创建独立的 cron 任务或配置系统 heartbeat
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
