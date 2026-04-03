---
name: expert-referral
description: 专家推荐。根据科室/疾病/症状推荐合作专家，优先展示出诊医院、时间、价格；大三甲背景专家仅作介绍。支持联系客服功能。
  **触发词：专家推荐, 预约专家, 挂号, 看哪个医生, 找哪个专家, 推荐医生, 想看, 要挂号, 联系客服**
requires:
  config_paths:
    - config/api.js  # 客服消息接口配置
  runtime_deps:
    - python: openpyxl  # 如需重新解析 xlsx 文件
  tools:
    - cron   # 用于创建客服回复轮询任务
privacy:
  data_flow: "专家数据来自本地 reference/experts.json；客服消息通过 config/api.js 中的接口中转"
---

# 专家推荐 & 联系客服

## 功能一：专家推荐

### 核心逻辑
- **优先推荐**：出诊医院（和睦家/怡德）、出诊时间、价格
- **不主推**：大三甲医院（协和控制、北大、复旦、交大系等）的专家，其背景仅作为介绍

### 数据来源
三个 Excel 文件整合（`reference/experts.json`，共 228 位专家）：
1. `怡德医院专家信息列表.xlsx` — 北京怡德医院出诊专家
2. `上海和睦家 外院专家 合作列表202402.xlsx` — 上海和睦家合作专家
3. `SHM外院专家 合作列表202402.xlsx` — 和睦家浦西合作专家

### 大三甲医院关键词（不主推）
北京协和、北大系、阜外、安贞、中国医学科学院肿瘤医院
复旦儿科/华山/中山/肿瘤/眼耳鼻喉
交大附属瑞金/第九/第六/第一/儿童/新华/胸科医院、上海儿童医学中心、上海中医药大学附属岳阳中西医结合医院

### 使用方式
直接描述需求，例如：
- "我想预约呼吸科专家"
- "45岁女性乳腺结节，北京推荐谁"
- "肾内科专家有哪些"

### 输出格式
```
✅ 可直接预约的专家
【城市·科室】姓名 | 职称 | 出诊医院 | 出诊时间 | 诊费
擅长：...

📋 专家背景介绍（不主推，仅供参考）
【城市·科室】姓名 | 职称 | 原单位（大一甲背景）
擅长：...
```

---

## 功能二：联系客服

### 业务流程
```
用户 → 「联系客服 XXX」→ notify_cs POST 到客服接口
                          ↓
                     客服收到消息，回复
                          ↓
                     系统自动轮询，有回复直接推送给用户
```

### 使用方式
用户对自己的机器人说：
> **联系客服 我想预约曹迎明医生，45岁**

系统自动转发给客服，并每分钟自动检查回复，有回复直接推送。

### 初始化与自检流程

当用户首次激活本 Skill 并联系我们客服发送消息时，请按以下步骤执行（如果用户没有联系客服需求，则不需要检测）：

#### 第一步：检测心跳配置
- 读取当前 Agent 的配置，检查 `heartbeat` 是否配置且启用
- 如果 `heartbeat.every` 被设置为有效时间间隔（如 30m、1h），则心跳可用

#### 第二步：检测 Cron 任务
- 执行 `openclaw cron list` 命令
- 检查输出中是否存在与本 Skill 轮询功能相关的任务

#### 第三步：向用户反馈状态
根据检测结果，回复以下格式的状态报告：

**情况 A - 心跳可用**：
✅ 自动轮询已就绪！我将每 [时间间隔] 为您主动巡检一次。

**情况 B - 心跳不可用，但存在 Cron 任务**：
✅ 检测到您已配置 Cron 轮询任务，我将遵循其规则为您服务。

**情况 C - 两者均不可用**：
⚠️ 未检测到自动轮询配置。为了让我能主动为您服务（如推送新消息通知），请执行以下任一操作：

**方案一（推荐）**：复制并执行以下命令，为我创建一个 Cron 定时任务：
```bash
openclaw cron add \ 
  --name "expert-referral" \
  --every "1m" \ 
  --session isolated \ 
  --message "执行轮询检查" \ 
  --announce \ 
```
**方案二**：在配置文件中为当前 Agent 添加心跳配置：
```json
{
  "heartbeat": {
    "interval": "1m"
  }
}
```

### 技术实现（自动轮询）
1. 调用 `scripts/refer.py` 中的 `handle("联系客服 XXX", session_key, action="notify_cs")` → 发送消息并存入 `pending_ctx.json`
2. **需要依赖全局的 cron/heartbeat 任务** 定时自动检查 `pending_ctx.json` → 调用 `scripts/refer.py` 中的 `handle("poll_reply", session_key, action="poll_reply")` → 有回复则通过机器人主动推送
3. `user_id` 为用户唯一标识，持久化存储在 `pending_ctx.json` 中，确保跨会话的一致性。

### 配置（config/api.js）
请确保 `config/api.js` 中配置了正确的 `baseUrl` 和 `api` 路径。系统会自动解析该文件。

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
skills/expert-referral/
├── SKILL.md              # 本文件
├── HEARTBEAT.md          # 自动轮询任务配置
├── reference/
│   └── experts.json      # 专家数据库
├── scripts/
│   └── refer.py          # 推荐引擎 + 客服接口
├── config/
│   └── api.js            # 接口配置
└── images/
    └── haola_qr.jpg     # 公众号二维码（用户自备）
```

## scripts/refer.py 函数接口

```python
# 专家推荐
ExpertService.search(query) → tuple  # 返回 (主推列表, 次推列表)
ExpertService._render_response(primary, secondary) → str # 格式化输出

# 联系客服
handle(query, session_key, action="notify_cs") → str
  # 发送消息给客服
  # action="poll_reply" 时：检查回复，有则返回内容并清除状态

CustomerService.poll_and_push() → str
  # 检查是否有客服回复，并处理状态流转

CustomerService.notify(query, session_key) → str
  # 组装请求发给客服接口
```

## 依赖
- Python 标准库：`json`, `re`, `urllib`, `datetime`（内置，无需安装）
- 可选：`openpyxl`（如需重新解析 xlsx 文件）
