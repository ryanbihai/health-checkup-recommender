#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文档提取脚本
从Excel文件中提取结构化数据
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

# 路径配置
BASE_DIR = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具')
INPUT_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '文档清单.json'
OUTPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据'

def extract_excel_data(filepath: Path) -> Dict[str, Any]:
    """从Excel文件提取数据"""
    result = {
        'filepath': str(filepath.relative_to(BASE_DIR)),
        'filename': filepath.name,
        'extract_time': datetime.now().isoformat(),
        'success': False,
        'sheets': [],
        'data': {}
    }
    
    try:
        # 读取所有Sheet
        excel_file = pd.ExcelFile(filepath)
        result['sheet_names'] = list(excel_file.sheet_names)
        
        for sheet_name in excel_file.sheet_names:
            try:
                # 读取Sheet数据
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                
                sheet_data = {
                    'sheet_name': sheet_name,
                    'rows': len(df),
                    'columns': list(df.columns),
                    'preview': df.head(5).to_dict('records') if len(df) > 0 else [],
                    'all_data': df.to_dict('records') if len(df) > 0 else []
                }
                
                # 尝试提取关键信息
                key_info = extract_key_info(df, sheet_name)
                if key_info:
                    sheet_data['key_info'] = key_info
                
                result['sheets'].append(sheet_data)
                result['data'][sheet_name] = sheet_data
                
            except Exception as e:
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'error': str(e)
                })
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def extract_key_info(df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
    """提取关键信息"""
    key_info = {
        'customer_name': None,
        'policy_info': [],
        'total_premium': None,
        'policies': []
    }
    
    # 转换为字符串便于搜索
    df_str = df.astype(str)
    
    # 查找客户姓名（常见列名）
    name_columns = ['姓名', '客户', '投保人', '被保险人', '受保人']
    for col in name_columns:
        if col in df.columns:
            for idx, val in df[col].items():
                if pd.notna(val) and str(val).strip():
                    key_info['customer_name'] = str(val).strip()
                    break
            if key_info['customer_name']:
                break
    
    # 查找保单信息
    policy_keywords = ['险种', '产品', '保障', '计划']
    for idx, row in df.iterrows():
        for col in df.columns:
            if any(keyword in str(col) for keyword in policy_keywords):
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    policy = {
                        'product': str(val).strip(),
                        'row': int(idx)
                    }
                    
                    # 尝试提取相关列
                    for related_col in df.columns:
                        if related_col != col:
                            related_val = row[related_col]
                            if pd.notna(related_val):
                                policy[str(related_col)] = str(related_val)
                    
                    key_info['policies'].append(policy)
                break
    
    # 计算总保费（如有）
    premium_columns = ['保费', '年缴', '缴费']
    for col in premium_columns:
        if col in df.columns:
            try:
                premiums = df[col].dropna()
                if len(premiums) > 0:
                    # 尝试转换为数值
                    numeric_premiums = pd.to_numeric(premiums, errors='coerce').dropna()
                    if len(numeric_premiums) > 0:
                        key_info['total_premium'] = float(numeric_premiums.sum())
                        break
            except:
                pass
    
    # 如果没有找到关键信息，返回None
    if not any([key_info['customer_name'], key_info['policies']]):
        return None
    
    return key_info

def guess_client_from_path(filepath: Path) -> str:
    """从文件路径猜测客户名"""
    parts = filepath.parts
    for part in parts:
        if '待整理档案' in parts:
            idx = parts.index('待整理档案')
            if idx + 1 < len(parts):
                return parts[idx + 1]
    return filepath.parent.name

class DateTimeEncoder(json.JSONEncoder):
    """处理datetime类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def convert_to_json_serializable(obj):
    """递归转换对象为JSON可序列化类型"""
    if isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

def main():
    """主函数"""
    print("=" * 60)
    print("Excel文档提取工具")
    print("=" * 60)
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 读取文档清单
    print(f"\n📖 读取文档清单...")
    if not INPUT_FILE.exists():
        print(f"❌ 文档清单不存在，请先运行 scan_documents.py")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        document_list = json.load(f)
    
    # 筛选Excel文件
    excel_files = []
    for client_data in document_list:
        for doc in client_data['documents']:
            if doc['file_type'] == 'excel':
                full_path = BASE_DIR / doc['filepath']
                if full_path.exists():
                    excel_files.append({
                        'client_name': client_data['client_name'],
                        'filepath': full_path,
                        'relative_path': doc['filepath'],
                        'filename': doc['filename']
                    })
    
    print(f"\n找到 {len(excel_files)} 个Excel文件")
    
    # 提取数据
    results = []
    success_count = 0
    error_count = 0
    
    print(f"\n📊 开始提取数据...")
    for i, file_info in enumerate(excel_files, 1):
        print(f"\n[{i:3d}/{len(excel_files)}] 提取: {file_info['filename']}")
        print(f"         客户: {file_info['client_name']}")
        
        result = extract_excel_data(file_info['filepath'])
        result['client_name'] = file_info['client_name']
        
        if result['success']:
            success_count += 1
            print(f"         ✅ 成功 - {len(result['sheets'])} 个Sheet")
            
            if result['sheets']:
                first_sheet = result['sheets'][0]
                print(f"         📋 首Sheet: {first_sheet['rows']} 行")
                
                if 'key_info' in first_sheet and first_sheet['key_info']:
                    key_info = first_sheet['key_info']
                    if key_info['customer_name']:
                        print(f"         👤 客户: {key_info['customer_name']}")
                    if key_info['policies']:
                        print(f"         📄 保单: {len(key_info['policies'])} 个")
        else:
            error_count += 1
            print(f"         ❌ 失败: {result.get('error', '未知错误')}")
        
        results.append(result)
    
    # 保存结果（转换datetime类型）
    output_file = OUTPUT_DIR / 'excel_extraction_results.json'
    print(f"\n\n💾 保存结果...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(convert_to_json_serializable(results), f, ensure_ascii=False, indent=2)
    
    # 保存客户汇总
    client_summary = {}
    for result in results:
        if result['success']:
            client_name = result['client_name']
            if client_name not in client_summary:
                client_summary[client_name] = {
                    'files': [],
                    'total_sheets': 0,
                    'customers': set(),
                    'policies': []
                }
            
            client_summary[client_name]['files'].append(result['filepath'])
            client_summary[client_name]['total_sheets'] += len(result['sheets'])
            
            # 提取客户名和保单
            for sheet in result['sheets']:
                if 'key_info' in sheet and sheet['key_info']:
                    key_info = sheet['key_info']
                    if key_info['customer_name']:
                        client_summary[client_name]['customers'].add(key_info['customer_name'])
                    if key_info['policies']:
                        client_summary[client_name]['policies'].extend(key_info['policies'])
    
    # 转换为可JSON格式
    for client_name in client_summary:
        client_summary[client_name]['customers'] = list(client_summary[client_name]['customers'])
        client_summary[client_name]['policies_count'] = len(client_summary[client_name]['policies'])
        del client_summary[client_name]['policies']
    
    summary_file = OUTPUT_DIR / 'excel_customer_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(convert_to_json_serializable(client_summary), f, ensure_ascii=False, indent=2)
    
    # 打印统计
    print("\n" + "=" * 60)
    print("✅ Excel提取完成！")
    print("=" * 60)
    
    print(f"\n📊 统计:")
    print(f"   总文件数: {len(excel_files)}")
    print(f"   成功: {success_count} ✅")
    print(f"   失败: {error_count} ❌")
    print(f"   成功率: {success_count/len(excel_files)*100:.1f}%")
    
    print(f"\n🏆 客户统计 (Top 10):")
    sorted_clients = sorted(client_summary.items(), key=lambda x: len(x[1]['files']), reverse=True)
    for i, (client_name, data) in enumerate(sorted_clients[:10], 1):
        print(f"   {i:2d}. {client_name:20s} - {len(data['files']):2d} 文件, {data['total_sheets']:2d} Sheet, {len(data['customers'])} 客户")
    
    print(f"\n💾 文件已保存:")
    print(f"   - 提取结果: {output_file}")
    print(f"   - 客户汇总: {summary_file}")

if __name__ == '__main__':
    main()
