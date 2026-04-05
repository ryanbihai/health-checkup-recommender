#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试：分析吴昱Excel第一个Sheet的结构
"""

import pandas as pd
from pathlib import Path
import traceback

filepath = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\吴昱\保单利益说明-吴昱20250629.xlsx')

print(f"分析文件: {filepath.name}")
print("="*80)

try:
    # 读取第一个Sheet
    sheet_name = "保单利益详细说明"
    print(f"\nSheet: {sheet_name}")
    
    # 读取前30行，不使用header
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    print(f"总行数: {len(df)}")
    print(f"总列数: {len(df.columns)}")
    
    # 显示前30行
    print("\n内容预览:")
    for idx in range(min(30, len(df))):
        row = df.iloc[idx]
        row_data = []
        for col_idx, val in enumerate(row):
            if pd.notna(val):
                val_str = str(val)[:50].replace('\n', ' ')
                row_data.append(f"[{col_idx}]{val_str}")
        if row_data:
            print(f"R{idx}: {' '.join(row_data)}")
    
    # 尝试使用header=0读取
    print("\n\n尝试使用header=0:")
    df2 = pd.read_excel(filepath, sheet_name=sheet_name, header=0)
    print(f"列名: {list(df2.columns)[:10]}")
    print("\n前5行:")
    print(df2.head())
    
except Exception as e:
    print(f"错误: {e}")
    traceback.print_exc()

# 尝试读取所有Sheet的前几行
print("\n\n" + "="*80)
print("所有Sheet预览:")
excel_file = pd.ExcelFile(filepath)
for sheet in excel_file.sheet_names:
    print(f"\n--- {sheet} ---")
    try:
        df = pd.read_excel(filepath, sheet_name=sheet, header=None)
        print(f"行数: {len(df)}, 列数: {len(df.columns)}")
        # 显示前3行
        for idx in range(min(3, len(df))):
            row = df.iloc[idx]
            vals = [str(v)[:30] for v in row if pd.notna(v)]
            if vals:
                print(f"  R{idx}: {' | '.join(vals[:5])}")
    except Exception as e:
        print(f"  错误: {e}")
