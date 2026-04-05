#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查列映射
"""

import pandas as pd
from pathlib import Path

filepath = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\吴昱\保单利益说明-吴昱20250629.xlsx')

print(f"分析文件: {filepath.name}")

sheet_name = "保单利益详细说明"

# 使用header=1读取
df = pd.read_excel(filepath, sheet_name=sheet_name, header=1, engine='openpyxl')

print(f"\n列名:")
for idx, col in enumerate(df.columns):
    print(f"  {idx}: '{col}'")

print(f"\n第一行数据:")
row = df.iloc[0]
for idx, (col, val) in enumerate(zip(df.columns, row)):
    if pd.notna(val):
        print(f"  {idx}: {col} = {val}")
