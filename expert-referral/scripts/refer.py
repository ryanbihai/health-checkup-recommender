#!/usr/bin/env python3
"""
专家推荐 Skill - 核心引擎

功能：
1. 专家推荐（基于 experts.json 搜索引擎）
2. 联系客服（异步消息推送 + 高频心跳巡检）
"""

import json, os, re, sys, textwrap, uuid
import urllib.request
import urllib.error
from datetime import datetime
from functools import lru_cache

# ─────────────────────────────────────────────
# 基础路径与常量
# ─────────────────────────────────────────────
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERTS_FILE = os.path.join(SKILL_DIR, "reference", "experts.json")
PENDING_FILE = os.path.join(SKILL_DIR, "pending_ctx.json")
CONFIG_JS_PATH = os.path.join(SKILL_DIR, "config", "api.js")

# 确保 pending_ctx.json 存在（用于存储持久化 user_id 和 咨询状态）
if not os.path.exists(PENDING_FILE):
    try:
        # 优先尝试从 .env 获取本地测试 ID
        env_id = None
        env_path = os.path.join(SKILL_DIR, ".env")
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("USER_ID="):
                        env_id = line.split("=", 1)[1].strip()
                        break
        
        initial_id = env_id if env_id else str(uuid.uuid4())[:8]
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump({"user_id": initial_id}, f, ensure_ascii=False, indent=2)
    except:
        pass

# ─────────────────────────────────────────────
# 配置管理 (ConfigManager)
# ─────────────────────────────────────────────

class ConfigManager:
    """负责从 JS 文件或环境变量中动态加载配置"""
    
    @staticmethod
    @lru_cache(maxsize=1)
    def load():
        """从 config/api.js 动态提取接口地址，实现 dev/prod 环境自动切换"""
        if not os.path.exists(CONFIG_JS_PATH):
            return {}

        try:
            with open(CONFIG_JS_PATH, encoding="utf-8") as f:
                content = f.read()
            
            # 提取 baseUrl (匹配 activeEnv 赋值后的最终值)
            base_urls = re.findall(r"baseUrl:\s*['\"]([^'\"]+)['\"]", content)
            if not base_urls:
                raise ValueError(f"CRITICAL: baseUrl not found in {CONFIG_JS_PATH}")
            base_url = base_urls[-1]
            
            # 提取 api 路径
            def extract_path(key):
                match = re.search(rf"{key}:\s*['\"]([^'\"]+)['\"]", content)
                if not match:
                    raise ValueError(f"CRITICAL: API path '{key}' not found in {CONFIG_JS_PATH}")
                return match.group(1)

            return {
                "cs_webhook_url": base_url + extract_path("sendMessage"),
                "cs_poll_url": f"{base_url}{extract_path('getReply')}?user_id=USER_SESSION_KEY"
            }
        except Exception as e:
            # 配置加载失败是致命错误，直接抛出，不再返回空字典
            raise RuntimeError(f"Failed to initialize configuration: {e}")

# ─────────────────────────────────────────────
# 状态与身份管理 (StateManager)
# ─────────────────────────────────────────────

class StateManager:
    """负责持久化状态（user_id 和咨询上下文）的管理"""

    @staticmethod
    def _get_env_user_id():
        """尝试从 .env 获取本地测试 ID"""
        env_path = os.path.join(SKILL_DIR, ".env")
        if os.path.exists(env_path):
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("USER_ID="):
                        return line.split("=", 1)[1].strip()
        return None

    @classmethod
    def get_user_id(cls):
        """获取持久化用户ID，保证唯一性"""
        # 1. 优先使用环境变量/本地测试 ID
        env_id = cls._get_env_user_id()
        if env_id: return env_id

        # 2. 其次使用已保存的 ID
        ctx = cls.load_pending()
        if ctx and ctx.get("user_id"):
            return ctx["user_id"]

        # 3. 如果没有找到 ID，生成并持久化新 ID
        new_id = str(uuid.uuid4())[:8]
        cls.save_pending(user_id=new_id)
        return new_id

    @staticmethod
    def load_pending():
        """加载当前等待中的咨询上下文"""
        if not os.path.exists(PENDING_FILE):
            return None
        try:
            with open(PENDING_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    @staticmethod
    def save_pending(**kwargs):
        """更新并保存咨询上下文"""
        ctx = StateManager.load_pending() or {}
        ctx.update(kwargs)
        # 确保基础字段存在
        if "user_id" not in ctx:
            ctx["user_id"] = str(uuid.uuid4())[:8]
        
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)

    @staticmethod
    def clear_session():
        """清理咨询会话，但保留用户身份 ID"""
        ctx = StateManager.load_pending()
        if ctx:
            preserved = {"user_id": ctx.get("user_id")}
            with open(PENDING_FILE, "w", encoding="utf-8") as f:
                json.dump(preserved, f, ensure_ascii=False, indent=2)

# ─────────────────────────────────────────────
# 专家推荐逻辑 (ExpertService)
# ─────────────────────────────────────────────

class ExpertService:
    @staticmethod
    @lru_cache(maxsize=1)
    def _load_data():
        with open(EXPERTS_FILE, encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def search(cls, query):
        if not query: return "请输入您想搜索的科室或疾病。"
        
        data = cls._load_data()
        experts = data["experts"]
        keywords = data.get("big3_keywords", [])

        # 评分系统
        scored = []
        q = query.lower()
        for e in experts:
            score = 0
            if e.get("dept")  and q in e["dept"].lower():  score += 10
            if e.get("name")  and q in e["name"].lower():  score += 8
            if e.get("skill") and q in e["skill"].lower(): score += 5
            if score > 0:
                scored.append((score, e))
        
        scored.sort(key=lambda x: -x[0])
        top = [e for _, e in scored[:24]]
        
        # 分类：优先展示合作专家 (非 big3)
        primary = [e for e in top if not any(k in (e.get("main_hospital") or "") for k in keywords)]
        secondary = [e for e in top if e not in primary]

        return cls._render_response(primary[:8], secondary[:5])

    @staticmethod
    def _render_response(primary, secondary):
        lines = []
        if primary:
            lines.append("✅ **可直接预约的专家**\n")
            for e in primary:
                lines.append(f"【{e['city']}·{e['dept']}】{e['name']} | {e.get('title','')} | 出诊：{e['practice_hospital']} | {e['schedule']} | 诊费：{e.get('fee','详询')}")
                if e.get("skill"): lines.append(f"擅长：{e['skill'][:80]}...")
                lines.append("")
        
        if secondary:
            lines.append("\n📋 **专家背景介绍（仅供了解）**\n")
            for e in secondary:
                lines.append(f"【{e['city']}·{e['dept']}】{e['name']} | {e.get('title','')} | 原单位：{e.get('main_hospital','')} | 出诊：{e['practice_hospital']}")
                if e.get("skill"): lines.append(f"擅长：{e['skill'][:60]}...")
                lines.append("")

        lines.extend([
            "\n---\n📞 **联系我们预约专家**",
            "1️⃣ 电话热线：**400-109-2838**",
            "2️⃣ 微信公众号：**好啦**",
            "3️⃣ 直接帮您联系客服：回复「联系客服」+ 您的需求"
        ])
        return "\n".join(lines)

# ─────────────────────────────────────────────
# 客服服务 (CustomerService)
# ─────────────────────────────────────────────

class CustomerService:
    @staticmethod
    def notify(query, session_key):
        cfg = ConfigManager.load()
        user_id = StateManager.get_user_id()
        payload = json.dumps({"user_id": user_id, "question": query}, ensure_ascii=False).encode("utf-8")
        
        req = urllib.request.Request(cfg["cs_webhook_url"], data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            StateManager.save_pending(user_session_key=session_key, original_message=query, created_at=datetime.now().isoformat(), poll_count=0)
            return {"ok": True}

    @staticmethod
    def poll_and_push():
        ctx = StateManager.load_pending()
        if not ctx or not ctx.get("user_session_key"): return None

        cfg = ConfigManager.load()
        poll_url = cfg.get("cs_poll_url", "").replace("USER_SESSION_KEY", ctx["user_id"])
        
        try:
            with urllib.request.urlopen(poll_url, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = (data.get("data", {}) or {}).get("reply") or data.get("reply")
                
                if reply:
                    push_data = json.dumps({"session_key": ctx["user_session_key"], "content": f"💬 **客服回复**：\n\n{reply}"}, ensure_ascii=False)
                    print(f"PUSH_MESSAGE:{push_data}")
                    StateManager.clear_session()
                    return f"💬 客服回复：\n\n{reply}"
        except Exception:
            pass

        # 轮询计数与清理
        count = ctx.get("poll_count", 0) + 1
        if count > 30: StateManager.clear_session()
        else: StateManager.save_pending(poll_count=count)
        return None

# ─────────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────────

def handle(query, session_key=None, action=None):
    if action == "notify_cs":
        res = CustomerService.notify(query, session_key)
        if res.get("ok"):
            return "✅ 您的请求已转达给客服，系统将自动推送回复，请稍候……"
        return f"⚠️ 消息发送失败：{res.get('error')}"

    if action == "poll_reply":
        return CustomerService.poll_and_push()

    return ExpertService.search(query)

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("用法: python3 refer.py [search|notify_cs|poll_reply] [参数...]")
        sys.exit(0)

    cmd = args[0]
    if cmd == "search": print(ExpertService.search(" ".join(args[1:])))
    elif cmd == "notify_cs": print(handle(" ".join(args[1:2]), args[2] if len(args)>2 else "debug_user", "notify_cs"))
    elif cmd == "poll_reply": print(handle(None, action="poll_reply") or "（暂无客服回复）")
