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
用户 → 「联系客服 XXX」→ POST 到客服接口
                          ↓
                     客服收到消息，回复
                          ↓
                     系统自动轮询，有回复直接推送给用户
```

### 使用方式
用户对自己的机器人说：
> **联系客服 我想预约XXX医生，45岁**

### 初始化与自检流程

当用户首次激活本 Skill 并联系客服发送消息时，请按以下步骤执行：

#### 第一步：检测心跳配置
- 读取当前 Agent 的配置，检查 `heartbeat` 是否配置且启用

#### 第二步：检测 Cron 任务
- 执行 `openclaw cron list` 命令检查是否存在轮询任务

#### 第三步：向用户反馈状态

**情况 A - 心跳可用**：
✅ 自动轮询已就绪！我将每 [时间间隔] 为您主动巡检一次。

**情况 B - 心跳不可用，但存在 Cron 任务**：
✅ 检测到您已配置 Cron 轮询任务，我将遵循其规则为您服务。

**情况 C - 两者均不可用**：
⚠️ 未检测到自动轮询配置。请执行以下任一操作：

**方案一（推荐）**：复制并执行以下命令，为我创建一个 Cron 定时任务：
```bash
openclaw cron add \ 
  --name "expert-referral" \
  --every "1m" \ 
  --session isolated \ 
  --message "执行轮询检查" \ 
  --announce \ 
  --channel [您配置的渠道名称] 
```
**方案二**：在配置文件中为当前 Agent 添加心跳配置：
```json
{
  "heartbeat": {
    "interval": "1m"
  }
}
```

### 技术实现
1. `handle("联系客服 XXX", session_key, action="notify_cs")` → 发送消息并存入 `pending_ctx.json`
2. 依赖全局 cron/heartbeat 任务轮询 `pending_ctx.json`
3. 有回复则通过机器人主动推送

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

## scripts/refer.py 函数接口

```python
# 专家推荐
ExpertService.search(query) → str
  # 按科室/疾病/症状搜索专家
  # 返回格式化推荐结果

# 联系客服
handle(query, session_key, action="notify_cs") → str
  # 发送消息给客服

handle(action="poll_reply") → str
  # 轮询客服回复，有则返回内容

CustomerService.notify(query, session_key) → dict
  # 组装请求发给客服接口

CustomerService.poll_and_push() → str
  # 检查客服回复并处理状态流转
```

---

## 依赖

- Python 标准库：`json`, `re`, `urllib`, `datetime`（内置）
- 可选：`openpyxl`（如需重新解析 xlsx 文件）
