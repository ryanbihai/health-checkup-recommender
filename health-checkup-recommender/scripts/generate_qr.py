#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体检预约二维码生成脚本

⚠️ 业务要求：生成带参数的链接，指向环境配置的 domain

Usage:
    python generate_qr.py [output_path] [welfareid] [ruleid]
    python generate_qr.py output.png w123 r456

依赖:
    pip install qrcode pillow
"""

import qrcode
import sys
import os

def get_domain():
    if os.environ.get('NODE_ENV') == 'development':
        return 'https://t.ihaola.com.cn'
    return 'https://www.ihaola.com.cn'

def build_qr_content(welfareid=None, ruleid=None):
    """
    生成二维码内容（带参数的预约链接）
    """
    domain = get_domain()
    url = f"{domain}/launch/haola/pe?urlsrc=brief"
    
    if welfareid:
        url += f"&welfareid={welfareid}"
    if ruleid:
        url += f"&ruleid={ruleid}"
        
    return url

def generate_qr(output_path=None, welfareid=None, ruleid=None):
    """
    生成体检预约二维码
    """
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), '..', '体检预约二维码.png')

    output_path = os.path.abspath(output_path)

    # 如果命令行有参数
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        
        if len(args) > 0:
            output_path = os.path.abspath(args[0])
        if len(args) > 1:
            welfareid = args[1]
        if len(args) > 2:
            ruleid = args[2]

    content = build_qr_content(welfareid, ruleid)

    print(f"[INFO] Generating QR code...")
    print(f"[INFO] Content preview:\n{content}\n")

    img = qrcode.make(content)
    img.save(output_path)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"[OK] QR saved: {output_path} ({size_kb} KB)")
    return output_path


if __name__ == '__main__':
    # --consent 参数检查
    args = sys.argv[1:]
    has_consent = '--consent' in args or '--consent=true' in args
    
    if has_consent:
        args = [arg for arg in args if not arg.startswith('--consent')]
    
    if not has_consent and len(args) > 0:
        print('\n❌ 拒绝执行: 未提供 --consent 参数。在生成预约二维码前，必须征得用户同意。')
        sys.exit(1)
    
    generate_qr()
