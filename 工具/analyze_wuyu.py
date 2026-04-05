#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析吴昱的Excel文件结构
"""

import pandas as pd
from pathlib import Path

# 分析吴昱的Excel文件
filepath = Path(r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\吴昱\保单利益说明-吴昱20250629.xlsx")

print("="*80)
print(f"文件: {filepath}")
print("="*80)

# 读取所有Sheet
excel_file = pd.ExcelFile(filepath)
print(f"Sheet数量: {len(excel_file.sheet_names)}")
print(f"Sheet名称: {excel_file.sheet_names}")

for sheet_name in excel_file.sheet_names:
    print(f"\n{'='*80}")
    print(f"Sheet: {sheet_name}")
    print("="*80)
    
    # 读取前10行，不使用header
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    print(f"总行数: {len(df)}")
    print(f"总列数: {len(df.columns)}")
    
    # 显示前15行
    print("\n前15行内容:")
    for idx in range(min(15, len(df))):
        row = df.iloc[idx]
        row_data = []
        for col_idx, val in enumerate(row):
            if pd.notna(val):
                val_str = str(val)[:40].replace('\n', ' ')
                row_data.append(f"Col{col_idx}:{val_str}")
        if row_data:
            print(f"Row {idx}: {' | '.join(row_data[:6])}")  # 只显示前6列
