#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试吴昱Excel文件修复
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
import extract_excel_v4 as ex

# 测试吴昱的文件
filepath = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\吴昱\保单利益说明-吴昱20250629.xlsx')

print(f"测试文件: {filepath.name}")
print("="*60)

result = ex.process_excel_file(filepath)

print(f"Success: {result['success']}")
print(f"Policies count: {len(result['policies'])}")
print(f"Customers: {result['customers']}")

print("\nSheets:")
for s in result['sheets']:
    print(f"  - {s}")

print("\nPolicies:")
for p in result['policies']:
    print(f"  {p}")
