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
    获取或生成持久化用户ID。
    首次使用时自动生成并写入 config.json，之后复用。
    """
    import uuid
    config = load_config()
    if not config:
        # 没有配置文件，临时生成
        return str(uuid.uuid4())[:8]

    user_id = config.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())[:8]
        config["user_id"] = user_id
        # 写回去（如果主 config 文件存在）
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        else:
            alt = os.path.join(os.path.dirname(SKILL_DIR), "expert-referral-config.json")
            if os.path.exists(alt):
                with open(alt, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
    return user_id

def save_pending(user_session_key, user_message):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "user_id": get_user_id(),      # 用持久化 user_id
            "user_session_key": user_session_key,  # 同时保留原始 session_key
            "original_message": user_message,
            "created_at": datetime.now().isoformat(),
            "poll_count": 0
        }, f, ensure_ascii=False, indent=2)

def load_pending():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None

def clear_pending():
    if os.path.exists(PENDING_FILE):
        os.remove(PENDING_FILE)

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
    检查客服回复。
    返回：str 有回复内容 | None 无回复
    """
    ctx = load_pending()
    if not ctx or not ctx.get("user_id"):
        return None

    result = poll_cs_reply(ctx["user_id"])
    if result.get("ok") and result.get("reply"):
        clear_pending()
        return f"💬 **客服回复**：\n\n{result['reply']}"

    # 轮询计数，超时清除
    ctx["poll_count"] = ctx.get("poll_count", 0) + 1
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False)
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
