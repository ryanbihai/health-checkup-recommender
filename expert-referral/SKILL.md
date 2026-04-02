---
name: expert-referral
description: 专家推荐。根据科室/疾病/症状推荐合作专家，优先展示出诊医院、时间、价格；大三甲背景专家仅作介绍。支持联系客服功能。
  **触发词：专家推荐, 预约专家, 挂号, 看哪个医生, 找哪个专家, 推荐医生, 想看, 要挂号, 联系客服**
requires:
  config_paths:
    - config.json  # 客服消息接口配置
  runtime_deps:
    - python: openpyxl  # 如需重新解析 xlsx 文件
  tools:
    - cron   # 用于创建客服回复轮询任务
privacy:
  data_flow: "专家数据来自本地 experts.json；客服消息通过 config.json 中的接口中转"
---

# 专家推荐 & 联系客服

## 功能一：专家推荐

### 核心逻辑
- **优先推荐**：出诊医院（和睦家/怡德）、出诊时间、价格
- **不主推**：大三甲医院（协和控制、北大、复旦、交大系等）的专家，其背景仅作为介绍

### 数据来源
三个 Excel 文件整合（`experts.json`，共 228 位专家）：
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

### 技术实现（自动轮询）
1. 调用 `refer.handle("联系客服 XXX", session_key, action="notify_cs")` → 发送消息并存入 `pending_ctx.json`
2. HEARTBEAT.md 每30分钟自动检查 `pending_ctx.json` → 调用 `refer.poll_cs_reply()` → 有回复则通过 `sessions_send` 推送

### 配置（config.json）
```json
{
  "cs_webhook_url": "https://your-server.com/skill/api/send_message",
  "cs_poll_url": "https://your-server.com/skill/api/get_reply?user_id=USER_SESSION_KEY"
}
```

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
├── refer.py              # 推荐引擎 + 客服接口
├── experts.json           # 专家数据库
├── config.json            # 接口配置（用户本地填写）
└── images/
    └── haola_qr.jpg     # 公众号二维码（用户自备）
```

## refer.py 函数接口

```python
# 专家推荐
refer.respond_experts(query) → str  # 返回格式化推荐结果

# 联系客服
refer.handle(query, session_key, action="notify_cs") → str
  # 发送消息给客服，自动启动轮询 cron
  # action="poll_reply" 时：检查回复，有则返回内容

refer.poll_cs_reply(session_key) → dict
  # {"ok": True/False, "reply": "回复内容或None"}

refer.notify_cs(message, session_key) → dict
  # {"ok": True/False, "error": "..."}
```

## 依赖
- Python 标准库：`json`, `re`, `urllib`, `datetime`（内置，无需安装）
- 可选：`openpyxl`（如需重新解析 xlsx 文件）
