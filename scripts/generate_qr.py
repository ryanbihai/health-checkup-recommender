#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体检预约二维码生成脚本（安全版 v2.0）

⚠️ 安全设计原则（与 generate_qr.js 完全一致）：
- 二维码内容不含任何可识别PII
- 不包含指向第三方的完整URL参数
- 二维码仅含只读预约码，供就诊时出示

Usage:
    python generate_qr.py [output_path] [item1] [item2] ...
    python generate_qr.py output.png 胃镜 低剂量螺旋CT

依赖:
    pip install qrcode pillow
"""

import qrcode
import sys
import os
import time as time_module

# 套餐代码映射表
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
    '基础套餐': 'BASE',
}


def encode_package(items=None):
    """生成只读预约码（不含任何PII）"""
    if not items:
        return 'HL-BASE'
    item_codes = [ITEMS_MAP.get(it, '') for it in items if it in ITEMS_MAP]
    timestamp = str(int(time_module.time())).upper()
    code = '-'.join(item_codes) if item_codes else 'BASE'
    return f'HL-{timestamp}-{code}'


def build_qr_content(items=None):
    """
    生成二维码内容（不含任何PII）
    ⚠️ 二维码仅含只读预约码，用户需携带身份证就诊
    """
    if items is None:
        items = []
    item_names = ' + '.join(items) if items else '基础套餐'
    short_code = encode_package(items)

    return (
        f"体检套餐预约\n"
        f"套餐：{item_names}\n"
        f"预约码：{short_code}\n"
        f"请至 www.ihaola.com.cn 出示本码预约\n"
        f"本码不含个人信息，请携带身份证就诊"
    )


def generate_qr(output_path=None, items=None):
    """
    生成体检预约二维码（安全版）

    Args:
        output_path: 输出文件路径，默认保存到脚本同目录下
        items: 套餐项目列表，如 ['胃镜', '低剂量螺旋CT']
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), '..', '体检预约二维码.png')

    output_path = os.path.abspath(output_path)

    # 如果命令行有参数（第一项是路径或套餐名）
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        # 第一项看起来像路径（含 .png/.jpg 等)
        if args[0].lower().endswith(('.png', '.jpg', '.jpeg')):
            output_path = os.path.abspath(args[0])
            items = args[1:]
        else:
            items = args

    content = build_qr_content(items)

    print(f"[INFO] Generating QR code (safe version, no PII)...")
    print(f"[INFO] Content preview:\n{content}\n")

    img = qrcode.make(content)
    img.save(output_path)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"[OK] QR saved: {output_path} ({size_kb} KB)")
    return output_path


if __name__ == '__main__':
    generate_qr()
