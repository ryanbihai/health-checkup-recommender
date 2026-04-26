# Add tasks below when you want the agent to check something periodically.

## 客服消息轮询任务

当触发系统心跳时，你需要主动检查当前用户的等待回复，并进行推送。

**第一步：提取当前用户信息**
从当前对话的系统上下文（环境变量或系统事件）中提取真实用户身份标识（`user_id`）。如果上下文无法提供，请忽略本次心跳。

**第二步：执行轮询指令**
使用提取到的 `user_id` 执行以下指令：
```bash
python3 scripts/refer.py poll_reply --user_id "提取出的真实用户身份" --consent=true
```

**执行规则（绝对指令）**：
1. 如果脚本输出 `HEARTBEAT_OK`，说明当前没有任何等待回复。你必须且只能将该标记原样输出 `HEARTBEAT_OK`，**绝对禁止生成任何其他文字**。
2. 如果脚本输出了真实的客服回复内容（如：`💬 **客服回复**：...`），你必须使用 `message` 工具（action=send）主动将消息推给该用户。
3. **发送失败重试逻辑（仅限 Feishu 渠道）**：
   - 如果是通过飞书 (feishu) 渠道发送且首次发送失败（HTTP 400 错误）时，将消息内容包装成飞书交互卡片格式后重试。
   - 卡片模板格式：
     ```json
     {
       "config": { "wide_screen_mode": true },
       "header": {
         "title": { "tag": "plain_text", "content": "💬 客服回复" },
         "template": "blue"
       },
       "elements": [{ "tag": "div", "text": { "tag": "lark_md", "content": "客服回复的具体内容" } }]
     }
     ```
   - 重试时将原始消息内容嵌入 `elements[0].text.content`，保持 `message` 参数与 `card` 参数同时传递。
4. 完成推送后输出 `HEARTBEAT_OK` 结束本轮心跳。
