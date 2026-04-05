#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文档提取脚本 v4 - 简化版
直接使用pandas的header参数读取标准表格
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd

# 路径配置
BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
INPUT_DIR = BASE_DIR / '待整理档案'
OUTPUT_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据' / 'excel_extraction_v4_results.json'

# 列名标准化映射（按关键词匹配）
COLUMN_PATTERNS = {
    # 保单号
    '保单号': ['保单号', '单号', '保单流水号'],
    # 保险公司
    '保险公司': ['保险公司', '公司'],
    # 投保人
    '投保人': ['投保人'],
    # 被保险人
    '被保险人': ['被保险人', '被保人'],
    # 受益人
    '受益人': ['受益人', '身故保险金受益人'],
    # 产品名称
    '产品名称': ['险种名称', '险种', '产品名称', '产品', '险种名称（主险）'],
    # 保额
    '保额': ['保障额度', '保额', '基本保额', '保险金额', '保障'],
    # 缴费年限
    '缴费年限': ['交费期间', '交费年期', '缴费期间', '缴费年期', '年期'],
    # 保费
    '保费': ['险种保费', '期交保费', '年交保费', '保费', '保费（元）'],
    # 生效日期
    '生效日期': ['生效日', '生效日期', '保单生效日', '承保日期'],
    # 保险期间
    '保险期间': ['保险期间', '保障期间'],
    # 销售渠道
    '销售渠道': ['销售渠道', '渠道'],
    # 保单状态
    '保单状态': ['保单状态', '状态'],
    # 银行账号
    '银行账号': ['交费账号', '银行账号', '账号'],
}

def find_header_row(df: pd.DataFrame) -> int:
    """查找列标题行"""
    # 通常列标题在第1行或第2行
    for idx in range(min(5, len(df))):
        row = df.iloc[idx]
        row_str = ' '.join([str(v) for v in row if pd.notna(v)])
        
        # 检查是否包含关键词
        keywords = ['投保人', '被保险人', '险种名称', '险种', '保额', '保障额度', '保费', '生效', '保险公司']
        match_count = sum(1 for kw in keywords if kw in row_str)
        
        if match_count >= 2:  # 至少匹配2个关键词
            return idx
    
    return 0  # 默认使用第0行

def normalize_column_name(col_name: str) -> str:
    """标准化列名"""
    if pd.isna(col_name):
        return ''
    col_name = str(col_name).strip()
    
    # 移除换行符和多余空格
    col_name = col_name.replace('\n', ' ').replace('\r', ' ')
    col_name = ' '.join(col_name.split())  # 合并多个空格为单个
    
    # 精确匹配 - 按优先级排序（先匹配更具体的）
    column_priority = [
        # 保单号相关
        ('保单号', ['保险公司/保单号', '保单号', '单号']),
        # 产品相关
        ('产品名称', ['险种名称', '产品名称']),
        # 保额相关
        ('保额', ['保障额度', '保额', '基本保额']),
        # 保费相关（先匹配总保费）
        ('累计保费', ['总保费']),
        ('保费', ['险种保费', '期交保费', '年交保费', '保费（元）']),
        # 缴费年限
        ('缴费年限', ['交费期间', '交费年期', '年期']),
        # 保险期间
        ('保险期间', ['保险期间', '保障期间']),
        # 日期
        ('生效日期', ['生效日', '生效日期']),
        # 渠道
        ('销售渠道', ['销售渠道', '渠道']),
        # 状态
        ('保单状态', ['保单状态', '状态']),
        # 账号
        ('银行账号', ['交费账号', '账号']),
        # 人员
        ('投保人', ['投保人']),
        ('被保险人', ['被保险人', '被保人']),
        ('受益人', ['受益人', '身故保险金受益人']),
        # 公司
        ('保险公司', ['保险公司']),
    ]
    
    for normalized, patterns in column_priority:
        for pattern in patterns:
            if pattern in col_name:
                return normalized
    
    return col_name

def detect_company_and_policy_number(text: str) -> Tuple[str, str]:
    """识别保险公司和保单号"""
    if not text or pd.isna(text):
        return '', ''
    text = str(text).replace('\n', ' ')
    
    companies = {
        '中美联泰大都会人寿': ['大都会', '都会', '中美联泰'],
        '中国人寿': ['中国人寿', '国寿'],
        '平安': ['平安'],
        '太平洋': ['太平洋', '太保'],
        '新华': ['新华'],
        '华夏': ['华夏'],
        '泰康': ['泰康'],
        '信泰': ['信泰'],
        '横琴': ['横琴'],
        '爱心': ['爱心'],
    }
    
    company = ''
    policy_number = ''
    
    # 先尝试识别公司
    for c, keywords in companies.items():
        for kw in keywords:
            if kw in text:
                company = c
                # 移除公司名称，获取保单号
                remaining = text.replace(kw, '').strip()
                # 保单号通常是纯数字或字母数字组合
                match = re.search(r'([A-Z0-9]{5,})', remaining)
                if match:
                    policy_number = match.group(1)
                elif remaining:
                    # 如果没有找到标准格式，直接使用剩余部分
                    policy_number = remaining
                return company, policy_number
    
    # 如果没有识别到公司，返回原始文本
    return '', text.strip()

def detect_company(text: str) -> str:
    """识别保险公司"""
    company, _ = detect_company_and_policy_number(text)
    return company

def extract_amount(text: str) -> str:
    """提取金额"""
    if not text or pd.isna(text):
        return ''
    text = str(text).replace('\n', ' ')
    
    # 模式1：X万
    match = re.search(r'(\d+(?:\.\d+)?)\s*万', text)
    if match:
        return f"{match.group(1)}万"
    
    # 模式2：纯数字
    match = re.search(r'^[\d,]+(?:\.\d+)?$', text.strip())
    if match:
        num = match.group().replace(',', '')
        if float(num) > 0:
            return num
    
    return text.strip()

def parse_value(value: Any) -> str:
    """解析单元格值"""
    if pd.isna(value):
        return ''
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    return str(value).replace('\n', ' ').strip()

def process_excel_file(filepath: Path) -> Dict[str, Any]:
    """处理单个Excel文件"""
    result = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'folder': filepath.parent.name,
        'extract_time': datetime.now().isoformat(),
        'success': False,
        'sheets': [],
        'policies': [],
        'customers': {},
    }
    
    try:
        excel_file = pd.ExcelFile(filepath)
        result['sheet_names'] = excel_file.sheet_names
        
        all_policies = []
        all_customers = {}
        
        for sheet_name in excel_file.sheet_names:
            try:
                # 先读取整个sheet，使用openpyxl引擎
                df_raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None, engine='openpyxl')
                
                if df_raw.empty:
                    continue
                
                # 找到列标题行
                header_row = find_header_row(df_raw)
                
                # 重新读取，使用正确的标题行
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row, engine='openpyxl')
                
                # 标准化列名
                original_columns = list(df.columns)
                normalized_columns = [normalize_column_name(col) for col in df.columns]
                df.columns = normalized_columns
                
                # 建立列名到索引的映射
                col_to_idx = {col: idx for idx, col in enumerate(normalized_columns) if col}
                
                # 提取保单
                sheet_policies = []
                for idx, row in df.iterrows():
                    policy = {}
                    
                    # 使用索引遍历所有列
                    for col_idx, (orig_col, norm_col) in enumerate(zip(original_columns, normalized_columns)):
                        value = row.iloc[col_idx] if col_idx < len(row) else None
                        if norm_col == '保单号':
                            # 尝试同时提取公司和保单号
                            company, policy_no = detect_company_and_policy_number(value)
                            if company:
                                policy['保险公司'] = company
                            if policy_no:
                                policy['保单号'] = policy_no
                            elif value:
                                # 如果无法分离，使用原始值
                                policy['保单号'] = parse_value(value)
                                # 尝试从原始值中提取公司
                                company = detect_company(value)
                                if company:
                                    policy['保险公司'] = company
                        elif norm_col == '保险公司':
                            company = detect_company(value)
                            if company:
                                policy['保险公司'] = company
                            elif value:
                                policy['保险公司'] = parse_value(value)
                        elif norm_col == '投保人':
                            name = parse_value(value)
                            if name:
                                policy['投保人'] = name
                                all_customers['投保人'] = name
                        elif norm_col == '被保险人':
                            name = parse_value(value)
                            if name:
                                policy['被保人'] = name
                                if '投保人' not in all_customers:
                                    all_customers['被保人'] = name
                        elif norm_col == '受益人':
                            if value:
                                policy['受益人'] = parse_value(value)
                        elif norm_col == '产品名称':
                            if value:
                                policy['产品名称'] = parse_value(value)
                        elif norm_col == '保额':
                            amount = extract_amount(value)
                            if amount:
                                policy['保额'] = amount
                        elif norm_col == '缴费年限':
                            if value:
                                policy['缴费年限'] = parse_value(value)
                        elif norm_col == '保费':
                            amount = extract_amount(value)
                            if amount:
                                policy['保费'] = amount
                        elif norm_col == '生效日期':
                            date = parse_value(value)
                            if date:
                                policy['生效日期'] = date
                        elif norm_col == '保险期间':
                            if value:
                                policy['保险期间'] = parse_value(value)
                        elif norm_col == '销售渠道':
                            if value:
                                policy['销售渠道'] = parse_value(value)
                        elif norm_col == '保单状态':
                            if value:
                                policy['保单状态'] = parse_value(value)
                    
                    # 只保留有意义的保单
                    # 排除注释行
                    skip_keywords = ['注释', '犹豫期', '说明', '提示', '备注']
                    skip_text = ' '.join([str(v) for v in policy.values() if v])
                    if any(kw in skip_text for kw in skip_keywords):
                        continue
                    
                    # 判断是否有有效信息
                    if policy.get('保单号') or policy.get('产品名称') or policy.get('投保人') or policy.get('保额'):
                        policy = {k: v for k, v in policy.items() if v}
                        if policy:
                            sheet_policies.append(policy)
                
                all_policies.extend(sheet_policies)
                
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'header_row': header_row,
                    'rows': len(df),
                    'policies_count': len(sheet_policies)
                })
                
            except Exception as e:
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'error': str(e)
                })
        
        result['policies'] = all_policies
        result['customers'] = all_customers
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """主函数"""
    print("=" * 70)
    print("Excel Document Extraction v4 - Simplified Standard Table Parser")
    print("=" * 70)
    
    # 扫描Excel文件
    excel_files = list(INPUT_DIR.rglob('*.xlsx')) + list(INPUT_DIR.rglob('*.xls'))
    excel_files = [f for f in excel_files if '~$' not in str(f)]
    
    print(f"\nScanning: {INPUT_DIR}")
    print(f"Found {len(excel_files)} Excel files\n")
    print("Processing...\n")
    
    results = []
    
    for idx, filepath in enumerate(excel_files, 1):
        result = process_excel_file(filepath)
        results.append(result)
        
        status = "[OK]" if result['success'] else "[FAIL]"
        policy_count = len(result.get('policies', []))
        
        print(f"[{idx:3d}/{len(excel_files)}] {filepath.parent.name}/{filepath.name[:30]}")
        print(f"         {status} Sheets:{len(result['sheets'])} Policies:{policy_count}")
        
        if policy_count > 0:
            print(f"         Sample:")
            for policy in result['policies'][:2]:
                product = policy.get('产品名称', 'N/A')[:20]
                company = policy.get('保险公司', '')[:10]
                amount = policy.get('保额', '')
                policy_no = policy.get('保单号', '')[:15]
                print(f"           - [{company}] {product} {amount} ({policy_no})")
        
        print()
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r['success'])
    total_policies = sum(len(r.get('policies', [])) for r in results)
    
    all_customers = set()
    for r in results:
        for c in r.get('customers', {}).values():
            if c:
                all_customers.add(c)
    
    print("=" * 70)
    print("Extraction Complete!")
    print()
    print(f"Total files: {total}")
    print(f"Success: {success}")
    print(f"Extracted policies: {total_policies}")
    print(f"Unique customers: {len(all_customers)}")
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
