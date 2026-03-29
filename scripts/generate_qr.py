#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体检预约二维码生成脚本
Usage: python generate_qr.py [output_path]
"""

import qrcode
import sys
import os

# 预约链接
BOOKING_URL = "https://www.ihaola.com.cn/partners/haola-2ca4db68-192a-f911-501a-f155af6f5772/pe/launching.html?fromLaunch=1&needUserInfo=1&code=021Zi8ll2TT6rh4JtTll2PuJNd0Zi8lL&state="

def generate_qr(output_path=None):
    """生成体检预约二维码"""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "体检预约二维码.png")
    
    output_path = os.path.abspath(output_path)
    
    print(f"正在生成二维码...")
    print(f"链接: {BOOKING_URL}")
    
    img = qrcode.make(BOOKING_URL)
    img.save(output_path)
    
    print(f"✅ 二维码已保存: {output_path}")
    return output_path

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else None
    generate_qr(output)
