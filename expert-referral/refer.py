#!/usr/bin/env python3
"""
专家推荐脚本
用法: python3 refer.py <搜索关键词>
"""

import json
import sys
import re

# 加载专家数据
with open("/Users/admin/projects/skills/expert-referral/experts.json", encoding="utf-8") as f:
    data = json.load(f)

experts = data["experts"]
BIG3_KEYWORDS = data["big3_keywords"]

def is_big3(hospital):
    if not hospital:
        return False
    return any(kw in hospital for kw in BIG3_KEYWORDS)

def normalize_fee(fee_str):
    """提取最低诊费数字"""
    if not fee_str:
        return None
    nums = re.findall(r'\d+', str(fee_str))
    return int(nums[0]) if nums else None

def match_score(expert, query):
    """计算专家与查询关键词的匹配得分"""
    query_lower = query.lower()
    score = 0
    if expert["dept"] and query_lower in expert["dept"].lower():
        score += 10
    if expert["name"] and query_lower in expert["name"].lower():
        score += 8
    if expert["skill"] and query_lower in expert["skill"].lower():
        score += 5
    if expert["title"] and query_lower in expert["title"].lower():
        score += 2
    return score

def format_fee(fee):
    """格式化诊费显示"""
    if not fee:
        return "详询"
    fee_str = str(fee)
    nums = re.findall(r'\d+', fee_str)
    if not nums:
        return fee_str
    return f"首诊{nums[0]}元"

def search_experts(query, limit=10):
    """
    搜索专家，返回两组：可主推的 + 仅作介绍的
    """
    if not query:
        return [], []

    scored = []
    for e in experts:
        score = match_score(e, query)
        if score > 0:
            scored.append((score, e))

    scored.sort(key=lambda x: -x[0])
    top = scored[:limit * 3] if scored else []

    primary = []   # 可主推（非大三甲）
    secondary = [] # 仅作介绍（大一甲）

    for score, e in top:
        if is_big3(e["main_hospital"]):
            secondary.append(e)
        else:
            primary.append(e)

    return primary[:limit], secondary[:limit]

def render(expert, show_main_hosp=False):
    """渲染单条专家信息"""
    parts = [
        f"【{expert['city']}·{expert['dept']}】{expert['name']}",
        f"{expert['title'] or ''}",
        f"出诊：{expert['practice_hospital']}",
        f"{expert['schedule']}",
        f"诊费：{format_fee(expert['fee'])}",
    ]
    if show_main_hosp and expert.get("main_hospital"):
        parts.append(f"（原单位：{expert['main_hospital']}）")
    return " | ".join(filter(None, parts))

def respond(query):
    """生成推荐回复"""
    primary, secondary = search_experts(query)

    lines = []

    if primary:
        lines.append("✅ **可直接预约的专家**\n")
        for e in primary:
            lines.append(render(e))
            if e["skill"]:
                lines.append(f"擅长：{e['skill'][:80]}...")
            lines.append("")
    else:
        lines.append("暂无完全匹配的非大三甲专家。")

    if secondary:
        lines.append("\n📋 **专家背景介绍（仅供了解）**\n")
        for e in secondary[:5]:
            lines.append(render(e, show_main_hosp=True))
            if e["skill"]:
                lines.append(f"擅长：{e['skill'][:60]}...")
            lines.append("")

    return "\n".join(lines)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    print(respond(query))
