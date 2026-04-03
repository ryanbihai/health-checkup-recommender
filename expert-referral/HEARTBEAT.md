---
# 客服回复轮询心跳配置
# 当存在等待回复的咨询（pending_ctx.json）时触发

on:
  heartbeat:
    # 默认 30 分钟一次作为兜底
    interval: 30m
  condition:
    # 只有当存在 pending_ctx.json 且其中包含待处理的 session_key 时才执行
    file_exists: pending_ctx.json

# 当触发时执行的操作
jobs:
  poll_reply:
    steps:
      - name: 检查客服回复
        # 核心逻辑：
        # 1. 运行 refer.py poll_reply 检查是否有回复
        # 2. 如果没有回复，则进入循环轮询（每分钟一次，持续 30 次）
        # 这样可以在不修改用户全局配置的情况下，实现高频轮询
        run: |
          for i in {1..30}; do
            REPLY=$(python3 refer.py poll_reply)
            if [[ "$REPLY" != *"（暂无客服回复）"* ]]; then
              # 发现回复，由 refer.py 内部处理推送并清除状态，此处直接退出
              echo "Found reply, exiting loop."
              exit 0
            fi
            echo "No reply yet (attempt $i), waiting 1m..."
            sleep 60
          done
---
