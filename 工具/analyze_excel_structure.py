#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件结构分析工具
随机抽查Excel文件，分析其结构特点
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

# 被抽查的Excel文件
EXCEL_FILES = [
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\高英\都会臻享+万能险账户.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\周迅\保单资料20220213.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\付博\保单利益整理表-付博20220901.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\刘延生\保单利益概要表-刘延生.xls",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\李泽华\保单利益说明－王兆宁.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\李国栋\李国栋先生家庭保单利益概要表2025.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\戴宁-张建芸\保单利益概要表-戴宁20220505.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\孙雅静\都会赢家利益演示表.xlsx",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\刘剑\保单利益概要表-刘剑-2025.xls",
    r"c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具\待整理档案\吴可卡\都会赢家终身.xlsx",
]

def analyze_excel_structure(filepath: str) -> Dict[str, Any]:
    """分析单个Excel文件的结构"""
    result = {
        'filepath': filepath,
        'filename': Path(filepath).name,
        'folder': Path(filepath).parent.name,
        'sheets': [],
        'structure_type': 'unknown',
        'has_label_value': False,
        'labels_found': [],
        'data_preview': ''
    }
    
    try:
        # 读取所有Sheet
        excel_file = pd.ExcelFile(filepath)
        result['sheet_names'] = excel_file.sheet_names
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                
                sheet_info = {
                    'sheet_name': sheet_name,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
                
                # 查找"标签：值"模式
                labels = []
                label_value_pairs = 0
                
                for idx, row in df.iterrows():
                    row_data = row.tolist()
                    for i in range(len(row_data) - 1):
                        cell1 = str(row_data[i]).strip() if pd.notna(row_data[i]) else ''
                        cell2 = str(row_data[i+1]).strip() if pd.notna(row_data[i+1]) else ''
                        
                        # 检查是否是"标签：值"模式
                        if (cell1.endswith('：') or cell1.endswith(':')) and cell2 and cell2 != 'nan':
                            label_name = cell1[:-1]
                            labels.append(label_name)
                            label_value_pairs += 1
                
                sheet_info['label_value_pairs'] = label_value_pairs
                sheet_info['labels'] = list(set(labels))
                
                if label_value_pairs > 0:
                    result['has_label_value'] = True
                    result['labels_found'].extend(labels)
                
                # 收集数据预览（前5行）
                if idx < 5:
                    result['data_preview'] += f"\n=== {sheet_name} ===\n"
                    result['data_preview'] += df.head(5).to_string() + "\n"
                
                result['sheets'].append(sheet_info)
                
            except Exception as e:
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'error': str(e)
                })
        
        # 判断结构类型
        if result['has_label_value']:
            if len(set(result['labels_found'])) > 5:
                result['structure_type'] = '多标签表单'
            else:
                result['structure_type'] = '简单标签表单'
        elif len(result['sheets']) > 1:
            result['structure_type'] = '多Sheet数据表'
        else:
            result['structure_type'] = '普通表格'
        
        # 去重标签
        result['labels_found'] = list(set(result['labels_found']))
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """主函数"""
    print("=" * 80)
    print("Excel文件结构分析工具")
    print("=" * 80)
    print()
    
    results = []
    
    for idx, filepath in enumerate(EXCEL_FILES, 1):
        print(f"\n[{idx}/10] 分析文件: {Path(filepath).name}")
        print("-" * 80)
        
        result = analyze_excel_structure(filepath)
        results.append(result)
        
        if 'error' in result:
            print(f"   ❌ 错误: {result['error']}")
            continue
        
        print(f"   📁 目录: {result['folder']}")
        print(f"   📊 Sheet数: {len(result['sheets'])}")
        print(f"   📋 Sheet列表: {', '.join(result['sheets'][0]['sheet_name'] for s in result['sheets'])}")
        print(f"   🔍 结构类型: {result['structure_type']}")
        
        if result['has_label_value']:
            print(f"   ✅ 包含'标签：值'模式")
            print(f"   📝 发现标签: {', '.join(result['labels_found'][:10])}")
            if len(result['labels_found']) > 10:
                print(f"      ...还有 {len(result['labels_found']) - 10} 个标签")
        else:
            print(f"   ❌ 不包含'标签：值'模式")
        
        if result['sheets']:
            sheet = result['sheets'][0]
            print(f"   📐 表格尺寸: {sheet['rows']} 行 x {sheet['columns']} 列")
    
    print("\n" + "=" * 80)
    print("📊 统计汇总")
    print("=" * 80)
    
    # 统计
    total = len(results)
    with_label_value = sum(1 for r in results if r.get('has_label_value'))
    structure_types = {}
    
    for result in results:
        stype = result.get('structure_type', 'unknown')
        structure_types[stype] = structure_types.get(stype, 0) + 1
    
    print(f"\n总文件数: {total}")
    print(f"包含'标签：值'模式: {with_label_value} ({with_label_value/total*100:.1f}%)")
    print(f"不包含'标签：值'模式: {total - with_label_value} ({(total - with_label_value)/total*100:.1f}%)")
    
    print(f"\n结构类型分布:")
    for stype, count in structure_types.items():
        print(f"  - {stype}: {count} 个")
    
    # 收集所有标签
    all_labels = []
    for result in results:
        all_labels.extend(result.get('labels_found', []))
    
    unique_labels = list(set(all_labels))
    
    print(f"\n发现的标签类型（共 {len(unique_labels)} 种）:")
    for label in sorted(unique_labels):
        count = all_labels.count(label)
        print(f"  - {label}: {count} 次")
    
    print("\n" + "=" * 80)
    print("💡 分析结论")
    print("=" * 80)
    
    if with_label_value / total > 0.7:
        print("\n✅ 大部分Excel文件采用'标签：值'格式")
        print("   建议：继续使用 extract_excel_v2.py 的'标签：值'识别策略")
    elif with_label_value / total > 0.3:
        print("\n⚠️ 部分Excel文件采用'标签：值'格式，部分采用普通表格格式")
        print("   建议：需要针对不同类型使用不同的解析策略")
    else:
        print("\n❌ 大部分Excel文件不采用'标签：值'格式")
        print("   建议：需要逐份分析每个Excel文件的结构")

if __name__ == '__main__':
    main()
