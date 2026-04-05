#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文档提取脚本 v3 - 标准表格解析版
采用标准表格格式解析策略
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import pandas as pd

# 路径配置
BASE_DIR = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具')
INPUT_DIR = BASE_DIR / '待整理档案'
OUTPUT_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据' / 'excel_extraction_v3_results.json'

# 列名标准化映射
COLUMN_MAPPING = {
    # 保险公司/保单号
    '保险公司/保单号': '保单号',
    '保险公司\n/保单号': '保单号',
    '保险公司': '保险公司',
    '保单号': '保单号',
    
    # 投保人/被保险人
    '投保人': '投保人',
    '被保险人': '被保险人',
    '身故保险金受益人': '受益人',
    '受益人': '受益人',
    
    # 产品信息
    '险种名称': '产品名称',
    '险种': '产品名称',
    '产品名称': '产品名称',
    
    # 金额
    '保障额度': '保额',
    '保障额度/给付': '保额',
    '保险金额': '保额',
    '基本保额': '保额',
    '保额': '保额',
    
    # 期间
    '保险期间': '保险期间',
    '交费期间': '缴费年限',
    '交费年期': '缴费年限',
    '缴费期间': '缴费年限',
    '交费年期（年龄）': '缴费年限',
    
    # 保费
    '险种保费': '保费',
    '期交保费': '保费',
    '年交保费': '保费',
    '保费': '保费',
    '总保费': '累计保费',
    
    # 日期
    '生效日': '生效日期',
    '保单生效日': '生效日期',
    '承保日期': '生效日期',
    '生效日期': '生效日期',
    
    # 其他
    '销售渠道': '销售渠道',
    '保单状态': '保单状态',
    '交费账号': '银行账号',
    '银行账号': '银行账号',
}

# 保险公司识别模式
INSURANCE_COMPANIES = {
    '中美联泰大都会人寿': ['大都会', '都会', '中美联泰'],
    '中国人寿': ['中国人寿', '国寿'],
    '平安': ['平安'],
    '太平洋': ['太平洋', '太保'],
    '新华': ['新华'],
    '泰康': ['泰康'],
    '华夏': ['华夏'],
    '信泰': ['信泰'],
    '横琴': ['横琴'],
    '爱心': ['爱心'],
    '阳光': ['阳光'],
    '信诚': ['信诚'],
}

def detect_insurance_company(text: str) -> str:
    """识别保险公司"""
    if not text:
        return ''
    text = str(text).replace('\n', ' ')
    for company, keywords in INSURANCE_COMPANIES.items():
        for keyword in keywords:
            if keyword in text:
                return company
    return ''

def extract_policy_number(text: str) -> str:
    """从文本中提取保单号"""
    if not text:
        return ''
    text = str(text).replace('\n', ' ')
    # 保单号通常是字母+数字组合
    match = re.search(r'([A-Z0-9]{8,20})', text)
    if match:
        return match.group(1)
    return text.strip()

def parse_date(value: Any) -> str:
    """解析日期"""
    if pd.isna(value):
        return ''
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, str):
        # 尝试解析字符串日期
        try:
            dt = pd.to_datetime(value)
            return dt.strftime('%Y-%m-%d')
        except:
            return value
    return str(value)

def extract_amount(text: str) -> str:
    """提取金额"""
    if not text:
        return ''
    text = str(text).replace('\n', ' ')
    
    # 模式1：X万
    match = re.search(r'(\d+(?:\.\d+)?)\s*万', text)
    if match:
        return f"{match.group(1)}万"
    
    # 模式2：X元
    match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*元', text)
    if match:
        return match.group(1).replace(',', '') + '元'
    
    # 模式3：纯数字
    match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', text)
    if match and float(match.group(1).replace(',', '')) > 0:
        return match.group(1)
    
    return text.strip()

def normalize_column_name(col_name: str) -> str:
    """标准化列名"""
    if pd.isna(col_name):
        return ''
    col_name = str(col_name).replace('\n', ' ').strip()
    return COLUMN_MAPPING.get(col_name, col_name)

def process_sheet(df: pd.DataFrame, sheet_name: str) -> List[Dict[str, Any]]:
    """处理单个Sheet"""
    if df.empty:
        return []
    
    # 查找列标题行
    header_row = None
    for idx in range(min(5, len(df))):
        row = df.iloc[idx]
        row_str = ' '.join([str(v) for v in row if pd.notna(v)])
        if any(keyword in row_str for keyword in ['投保人', '被保险人', '险种', '保额', '保费']):
            header_row = idx
            break
    
    if header_row is None:
        # 如果找不到标题行，假设第0行或第1行是标题
        header_row = 0 if 'Unnamed' in str(df.columns[0]) else 1
    
    # 重新读取，使用正确的标题行
    try:
        df_data = pd.read_excel(Path('.'), sheet_name=sheet_name, header=header_row)
    except:
        df_data = df.copy()
    
    # 标准化列名
    df_data.columns = [normalize_column_name(col) for col in df_data.columns]
    
    policies = []
    
    # 获取需要的列
    cols = df_data.columns.tolist()
    
    for idx, row in df_data.iterrows():
        # 跳过空行或标题行
        if pd.isna(row.get('投保人')) and pd.isna(row.get('被保险人')):
            # 检查是否是保单号行（附加险可能在同一保单下）
            if pd.isna(row.get('产品名称')) and pd.isna(row.get('保额')):
                continue
        
        policy = {}
        
        # 提取保单号和保险公司
        policy_number = row.get('保单号', '')
        if policy_number and pd.notna(policy_number):
            policy_number = str(policy_number).replace('\n', ' ')
            company = detect_insurance_company(policy_number)
            if company:
                policy['保险公司'] = company
            policy['保单号'] = extract_policy_number(policy_number)
        elif pd.notna(row.get('保险公司')):
            company = detect_insurance_company(row.get('保险公司', ''))
            if company:
                policy['保险公司'] = company
            else:
                policy['保险公司'] = str(row.get('保险公司', '')).replace('\n', ' ')
        
        # 提取投保人/被保险人
        if pd.notna(row.get('投保人')):
            policy['投保人'] = str(row['投保人']).strip()
        if pd.notna(row.get('被保险人')):
            policy['被保人'] = str(row['被保险人']).strip()
        if pd.notna(row.get('受益人')):
            policy['受益人'] = str(row['受益人']).strip().replace('\n', ' ')
        
        # 提取产品名称
        if pd.notna(row.get('产品名称')):
            policy['产品名称'] = str(row['产品名称']).strip().replace('\n', ' ')
        
        # 提取保额
        if pd.notna(row.get('保额')):
            policy['保额'] = extract_amount(str(row['保额']))
        
        # 提取缴费年限
        if pd.notna(row.get('缴费年限')):
            policy['缴费年限'] = str(row['缴费年限']).strip().replace('\n', ' ')
        
        # 提取保费
        if pd.notna(row.get('保费')):
            policy['保费'] = extract_amount(str(row['保费']))
        
        # 提取生效日期
        if pd.notna(row.get('生效日期')):
            policy['生效日期'] = parse_date(row['生效日期'])
        
        # 提取保险期间
        if pd.notna(row.get('保险期间')):
            policy['保险期间'] = str(row['保险期间']).strip().replace('\n', ' ')
        
        # 提取销售渠道
        if pd.notna(row.get('销售渠道')):
            policy['销售渠道'] = str(row['销售渠道']).strip()
        
        # 提取保单状态
        if pd.notna(row.get('保单状态')):
            policy['保单状态'] = str(row['保单状态']).strip()
        
        # 提取银行账号
        if pd.notna(row.get('银行账号')):
            policy['银行账号'] = str(row['银行账号']).strip().replace('\n', ' ')
        
        # 如果有有效信息，添加到列表
        if policy.get('保单号') or policy.get('产品名称') or policy.get('投保人'):
            # 过滤空值
            policy = {k: v for k, v in policy.items() if v}
            if policy:
                policies.append(policy)
    
    return policies

def extract_info_from_filename(filename: str) -> Dict[str, str]:
    """从文件名提取保单信息"""
    info = {
        '保险公司': '',
        '产品名称': '',
        '保额': '',
        '缴费年限': '',
        '来源文件名': filename
    }
    
    # 保险公司识别
    detected = detect_insurance_company(filename)
    if detected:
        info['保险公司'] = detected
    
    # 保额提取
    amount_match = re.search(r'(\d+)\s*万', filename)
    if amount_match:
        info['保额'] = f"{amount_match.group(1)}万"
    
    # 年限提取
    year_match = re.search(r'(\d+)\s*年', filename)
    if year_match:
        info['缴费年限'] = f"{year_match.group(1)}年"
    
    # 产品名称提取
    product_patterns = [
        r'都会[^\s]+',
        r'大富翁[^\s]+',
        r'守护神[^\s]+',
        r'锦绣传承[^\s]+',
        r'传世[^\s]+',
        r'花样年华[^\s]+',
        r'臻享[^\s]+',
        r'赢家[^\s]+',
        r'天使[^\s]+',
    ]
    
    for pattern in product_patterns:
        product_match = re.search(pattern, filename)
        if product_match:
            info['产品名称'] = product_match.group(0)
            break
    
    return info

def process_excel_file(filepath: Path) -> Dict[str, Any]:
    """处理单个Excel文件"""
    result = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'extract_time': datetime.now().isoformat(),
        'success': False,
        'sheets': [],
        'policies': [],
        'customers': {},
        'filename_info': {}
    }
    
    try:
        # 读取所有Sheet
        excel_file = pd.ExcelFile(filepath)
        result['sheet_names'] = excel_file.sheet_names
        
        for sheet_name in excel_file.sheet_names:
            try:
                # 尝试读取Sheet
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                
                if df.empty:
                    continue
                
                # 处理Sheet
                sheet_policies = process_sheet(df, sheet_name)
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'rows': len(df),
                    'policies_count': len(sheet_policies)
                })
                
                result['policies'].extend(sheet_policies)
                
            except Exception as e:
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'error': str(e)
                })
        
        # 从文件名提取信息
        result['filename_info'] = extract_info_from_filename(filepath.name)
        
        # 补充文件名中的信息到保单
        if not result['policies'] and result['filename_info'].get('产品名称'):
            result['policies'].append({
                '保险公司': result['filename_info'].get('保险公司', ''),
                '产品名称': result['filename_info'].get('产品名称', ''),
                '保额': result['filename_info'].get('保额', ''),
                '缴费年限': result['filename_info'].get('缴费年限', ''),
                '来源文件': filepath.name
            })
        
        # 提取客户信息
        for policy in result['policies']:
            if policy.get('投保人'):
                result['customers']['投保人'] = policy['投保人']
            if policy.get('被保人'):
                result['customers']['被保人'] = policy['被保人']
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """主函数"""
    print("=" * 70)
    print("Excel文档提取工具 v3 - 标准表格解析版")
    print("=" * 70)
    
    # 扫描Excel文件
    excel_files = list(INPUT_DIR.rglob('*.xlsx')) + list(INPUT_DIR.rglob('*.xls'))
    excel_files = [f for f in excel_files if '~$' not in str(f)]
    
    print(f"\n📂 扫描目录: {INPUT_DIR}")
    print(f"找到 {len(excel_files)} 个Excel文件\n")
    print("📊 开始提取...\n")
    
    results = []
    
    for idx, filepath in enumerate(excel_files, 1):
        result = process_excel_file(filepath)
        results.append(result)
        
        status = "✅" if result['success'] else "❌"
        policy_count = len(result.get('policies', []))
        
        # 显示进度
        print(f"[{idx:3d}/{len(excel_files)}] {filepath.parent.name}/{filepath.name}")
        print(f"         {status} 成功")
        
        if policy_count > 0:
            print(f"         📋 保单: {policy_count} 个")
            for policy in result['policies'][:3]:
                product = policy.get('产品名称', policy.get('险种', '未知'))[:20]
                company = policy.get('保险公司', '')[:10]
                amount = policy.get('保额', '')
                policy_no = policy.get('保单号', '')[:15]
                print(f"            - [{company}] {product} {amount} ({policy_no})")
        
        if result.get('customers'):
            for key, value in result['customers'].items():
                print(f"         👤 {key}: {value}")
        
        print()
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r['success'])
    total_policies = sum(len(r.get('policies', [])) for r in results)
    
    # 统计客户
    all_customers = set()
    for r in results:
        for c in r.get('customers', {}).values():
            if c:
                all_customers.add(c)
    
    print("=" * 70)
    print("✅ Excel文档提取完成！")
    print()
    print("📊 统计:")
    print(f"   总文件数: {total}")
    print(f"   成功: {success} ✅")
    print(f"   失败: {total - success} ❌")
    print(f"   成功率: {success/total*100:.1f}%")
    print(f"   提取保单: {total_policies} 个")
    print(f"   涉及客户: {len(all_customers)} 人")
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 文件已保存: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
