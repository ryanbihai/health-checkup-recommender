#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体检预约二维码生成脚本（安全版）

⚠️ 安全设计原则：
- 二维码内容为本地显示用，不包含指向第三方的完整URL
- 不向第三方传递任何用户健康数据
- 二维码仅包含套餐摘要，供用户预约时出示

Usage: python generate_qr.py [output_path]
"""

import qrcode
import sys
import os
import time
import json

ITEMS_MAP = {
    '胃镜': 'G01',
    '肠镜': 'G02',
    '低剂量螺旋CT': 'G03',
    '前列腺特异抗原': 'G04',
    '心脏彩超': 'G05',
    '同型半胱氨酸': 'G06',
    '肝纤维化检测': 'G07',
    '糖化血红蛋白': 'G08',
    '颈动脉彩超': 'G09',
    '冠状动脉钙化积分': 'G10',
    '乳腺彩超+钼靶': 'G11',
    'TCT+HPV': 'G12',
}

def encode_package(items=None):
    """生成套餐只读摘要（不含PII）"""
    items = items or []
    item_codes = [ITEMS_MAP.get(it, '') for it in items if it in ITEMS_MAP]
    timestamp = int(time.time()).toString(36).upper()
    code = '-'.join(item_codes) if item_codes else 'BASE'
    return f"HL-{timestamp}-{code}"

def build_qr_content(items=None):
    """生成二维码内容（不含任何PII）"""
    items = items or []
    item_names = ' + '.join(items) if items else '基础套餐'
    short_code = encode_package(items)
    return (
        f"体检套餐预约\n"
        f"套餐：{item_names}\n"
        f"预约码：{short_code}\n"
        f"请至 www.ihaola.com.cn 出示本码预约\n"
        f"本码不含个人信息，请携带身份证就诊"
    )

def generate_qr(output_path=None):
    """生成体检预约二维码（安全版）"""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "体检预约二维码.png")
    
    output_path = os.path.abspath(output_path)
    
    # 检查是否有命令行参数作为套餐项目
    items = sys.argv[2:] if len(sys.argv) > 2 else []
    
    content = build_qr_content(items)
    
    print(f"正在生成二维码（安全版，不含PII）...")
    print(f"内容预览:\n{content}")
    
    img = qrcode.make(content)
    img.save(output_path)
    
    print(f"二维码已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else None
    generate_qr(output)
