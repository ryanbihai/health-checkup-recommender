#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试吴昱Excel文件
"""

import pandas as pd
from pathlib import Path
import traceback

filepath = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\吴昱\保单利益说明-吴昱20250629.xlsx')

print(f"分析文件: {filepath.name}")
print("="*80)

sheet_name = "保单利益详细说明"

try:
    # Step 1: 读取原始数据
    print("\nStep 1: 读取原始数据")
    df_raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None, engine='openpyxl')
    print(f"  行数: {len(df_raw)}, 列数: {len(df_raw.columns)}")
    print(f"  前5行:")
    for idx in range(min(5, len(df_raw))):
        row = df_raw.iloc[idx]
        non_null = [(i, str(v)[:30]) for i, v in enumerate(row) if pd.notna(v)]
        print(f"    R{idx}: {non_null}")
    
    # Step 2: 找到标题行
    print("\nStep 2: 查找标题行")
    for idx in range(min(5, len(df_raw))):
        row = df_raw.iloc[idx]
        row_str = ' '.join([str(v) for v in row if pd.notna(v)])
        keywords = ['投保人', '被保险人', '险种名称', '险种', '保额', '保障额度', '保费', '生效', '保险公司']
        match_count = sum(1 for kw in keywords if kw in row_str)
        print(f"  R{idx}: 匹配 {match_count} 个关键词")
        if match_count >= 2:
            print(f"    -> 使用 R{idx} 作为标题行")
            header_row = idx
            break
    
    # Step 3: 使用标题行读取数据
    print("\nStep 3: 使用标题行读取数据")
    df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row, engine='openpyxl')
    print(f"  列名: {list(df.columns)}")
    print(f"  行数: {len(df)}")
    
    # Step 4: 标准化列名
    print("\nStep 4: 标准化列名")
    normalized_cols = []
    for col in df.columns:
        col_str = str(col).replace('\n', ' ').replace('\r', ' ')
        col_str = ' '.join(col_str.split())
        print(f"  '{col}' -> '{col_str}'")
        normalized_cols.append(col_str)
    
    # Step 5: 遍历数据行
    print("\nStep 5: 遍历数据行")
    print(f"  共 {len(df)} 行")
    
    for idx, row in df.iterrows():
        print(f"  处理行 {idx}:")
        row_dict = row.to_dict()
        print(f"    原始: {row_dict}")
        break  # 只处理第一行
        
except Exception as e:
    print(f"\n错误: {e}")
    traceback.print_exc()
