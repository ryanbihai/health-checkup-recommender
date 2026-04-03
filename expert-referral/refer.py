#!/usr/bin/env python3
"""
专家推荐 Skill - 核心引擎

功能：
1. 专家推荐（见 experts.json）
2. 联系客服：POST 消息给客服 + 自动创建 cron 轮询
"""

import json, os, re, sys, textwrap
import urllib.request
import urllib.error
from datetime import datetime

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SKILL_DIR, "config.json")
EXPERTS_FILE = os.path.join(SKILL_DIR, "experts.json")
PENDING_FILE = os.path.join(SKILL_DIR, "pending_ctx.json")

# ─────────────────────────────────────────────
# 配置文件
# ─────────────────────────────────────────────

def load_config():
    path = CONFIG_FILE
    if not os.path.exists(path):
        alt = os.path.join(os.path.dirname(SKILL_DIR), "expert-referral-config.json")
        if os.path.exists(alt):
            path = alt
        else:
            return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_user_id():
    """
    获取或生成持久化用户ID，优先级：
    1. .env 中的 USER_ID（本地测试用）
    2. pending_ctx.json 中的 user_id
    3. 新生成并写入 pending_ctx.json
    """
    import uuid

    # 优先级1：.env 文件
    env_path = os.path.join(SKILL_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("USER_ID="):
                    val = line.split("=", 1)[1].strip()
                    if val:
                        return val

    # 优先级2：从 pending_ctx.json 读取
    ctx = load_pending() or {}
    if ctx.get("user_id"):
        return ctx["user_id"]

    # 优先级3：生成新ID并存入 pending_ctx.json
    new_id = str(uuid.uuid4())[:8]
    ctx["user_id"] = new_id
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False, indent=2)
    return new_id

def save_pending(user_session_key, user_message):
    ctx = load_pending() or {}
    ctx.update({
        "user_id": get_user_id(),
        "user_session_key": user_session_key,
        "original_message": user_message,
        "created_at": datetime.now().isoformat(),
        "poll_count": 0
    })
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False, indent=2)

def load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

def clear_pending():
    """清理咨询相关的上下文，但保留 user_id"""
    ctx = load_pending()
    if ctx:
        # 只保留 user_id，清除其他咨询相关的字段
        preserved = {"user_id": ctx.get("user_id")}
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(preserved, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# 专家推荐
# ─────────────────────────────────────────────

def load_experts():
    with open(EXPERTS_FILE, encoding="utf-8") as f:
        return json.load(f)["experts"]

def is_big3(hospital):
    if not hospital:
        return False
    with open(EXPERTS_FILE, encoding="utf-8") as f:
        keywords = json.load(f)["big3_keywords"]
    return any(kw in hospital for kw in keywords)

def match_score(expert, query):
    q = query.lower()
    s = 0
    if expert.get("dept")  and q in expert["dept"].lower():   s += 10
    if expert.get("name")   and q in expert["name"].lower():   s += 8
    if expert.get("skill")  and q in expert["skill"].lower():   s += 5
    if expert.get("title")  and q in expert["title"].lower():   s += 2
    return s

def format_fee(fee):
    if not fee:
        return "详询"
    nums = re.findall(r'\d+', str(fee))
    return f"首诊{nums[0]}元" if nums else str(fee)

def render(expert, show_main_hosp=False):
    parts = [
        f"【{expert['city']}·{expert['dept']}】{expert['name']}",
        f"{expert.get('title', '')}",
        f"出诊：{expert['practice_hospital']}",
        f"{expert['schedule']}",
        f"诊费：{format_fee(expert.get('fee'))}",
    ]
    if show_main_hosp and expert.get("main_hospital"):
        parts.append(f"（原单位：{expert['main_hospital']}）")
    return " | ".join(filter(None, parts))

def search_experts(query, limit=8):
    experts = load_experts()
    if not query:
        return [], []
    scored = sorted([(match_score(e, query), e) for e in experts], key=lambda x: -x[0])
    top = [e for _, e in scored[:limit * 3]]
    primary   = [e for e in top if not e.get("big3")]
    secondary = [e for e in top if     e.get("big3")]
    return primary[:limit], secondary[:limit]

def respond_experts(query):
    primary, secondary = search_experts(query)
    lines = []
    if primary:
        lines.append("✅ **可直接预约的专家**\n")
        for e in primary:
            lines.append(render(e))
            if e.get("skill"):
                lines.append(f"擅长：{e['skill'][:80]}...")
            lines.append("")
    else:
        lines.append("暂无完全匹配的非大三甲专家。")
    if secondary:
        lines.append("\n📋 **专家背景介绍（仅供了解）**\n")
        for e in secondary[:5]:
            lines.append(render(e, show_main_hosp=True))
            if e.get("skill"):
                lines.append(f"擅长：{e['skill'][:60]}...")
            lines.append("")
    lines.append("\n---\n")
    lines.append("📞 **联系我们预约专家**\n")
    lines.append("1️⃣ 电话热线：**400-109-2838**\n")
    lines.append("2️⃣ 微信公众号：**好啦**（搜一搜关注后留言）\n")
    lines.append("3️⃣ 直接帮您联系客服：**告诉我「联系客服」+ 想问的问题**")
    return "\n".join(lines)

# ─────────────────────────────────────────────
# 联系客服
# ─────────────────────────────────────────────

def notify_cs(user_query, session_key=None):
    """POST 消息给客服，user_id 使用持久化 ID"""
    config = load_config()
    if not config or not config.get("cs_webhook_url"):
        return {"ok": False, "error": "未配置 cs_webhook_url"}

    user_id = get_user_id()
    payload = json.dumps({
        "user_id": user_id,
        "question": user_query
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        config["cs_webhook_url"],
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"ok": True, "status": resp.status}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def poll_cs_reply(session_key=None):
    """GET 轮询客服回复，user_id 使用持久化 ID"""
    config = load_config()
    if not config or not config.get("cs_poll_url"):
        return {"ok": False, "reply": None}

    user_id = get_user_id()
    poll_url = config["cs_poll_url"].replace("USER_SESSION_KEY", user_id)
    req = urllib.request.Request(poll_url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            reply = (data.get("data", {}) or {}).get("reply") if isinstance(data.get("data"), dict) else data.get("reply")
            return {"ok": True, "reply": reply}
    except Exception:
        return {"ok": False, "reply": None}

def check_and_push_reply():
    """
    检查客服回复并推送。
    返回：str 有回复内容 | None 无回复
    """
    ctx = load_pending()
    if not ctx or not ctx.get("user_id") or not ctx.get("user_session_key"):
        return None

    result = poll_cs_reply()
    if result.get("ok") and result.get("reply"):
        reply_content = result["reply"]
        
        # 使用 sessions_send 实现主动推送（OpenClaw 支持）
        try:
            # 这里的 payload 需要包含推送目标和消息
            push_payload = json.dumps({
                "session_key": ctx["user_session_key"],
                "content": f"💬 **客服回复**：\n\n{reply_content}"
            }, ensure_ascii=False).encode("utf-8")
            
            # 注意：推送接口通常由环境注入或有特定 URL，此处假设由 Skill 框架内部处理
            # 也可以通过 print 输出特定格式让 OpenClaw 捕获并推送
            print(f"PUSH_MESSAGE:{push_payload.decode('utf-8')}")
        except Exception as e:
            # 推送失败时保留 ctx，下次继续尝试
            return f"Error pushing: {str(e)}"

        clear_pending()
        return f"💬 **客服回复**：\n\n{reply_content}"

    # 轮询计数（由 HEARTBEAT.md 控制高频轮询时，这里的计数代表总尝试次数）
    ctx["poll_count"] = ctx.get("poll_count", 0) + 1
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False, indent=2)
    
    # 限制总轮询时长（例如 30 次 * 1分钟 = 30 分钟）
    if ctx["poll_count"] > 30:
        clear_pending()
    return None

# ─────────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────────

def handle(query, session_key=None, action=None):
    """
    主入口
    - action=None        → 专家推荐
    - action="notify_cs" → 发送消息给客服 + 自动创建轮询 cron
    - action="poll_reply" → 检查客服回复
    """
    if action == "notify_cs":
        result = notify_cs(query, session_key=get_user_id())
        if result.get("ok"):
            save_pending(session_key, query)
            return (
                f"✅ 您的请求已转达给客服，客服将直接回复您。\n"
                f"系统将自动推送客服回复，请稍候……\n\n"
                f"（每次会话仅限一次联系客服，如需再次联系请重新发起）"
            )
        else:
            return f"⚠️ 消息发送失败：{result.get('error')}"

    if action == "poll_reply":
        return check_and_push_reply()

    return respond_experts(query)

# ─────────────────────────────────────────────
# CLI 调试
# ─────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(textwrap.dedent("""
            用法:
              python3 refer.py search <关键词>
              python3 refer.py notify_cs <消息> [session_key]
              python3 refer.py poll_reply
        """).strip())
        sys.exit(0)

    cmd = args[0]
    if cmd == "search" and len(args) >= 2:
        print(respond_experts(" ".join(args[1:])))
    elif cmd == "notify_cs" and len(args) >= 2:
        key = args[2] if len(args) >= 3 else f"debug_{os.environ.get('USER','user')}"
        msg = args[1]
        print(handle(msg, session_key=key, action="notify_cs"))
    elif cmd == "poll_reply":
        result = handle(None, action="poll_reply")
        print(result if result else "（暂无客服回复）")
    else:
        print("参数不足")
