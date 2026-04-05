#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文档提取脚本 v2 - 修复版
专门处理"标签：值"格式的Excel文件
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
OUTPUT_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据' / 'excel_extraction_v2_results.json'

# 保险公司识别模式
INSURANCE_COMPANIES = {
    '中国人寿': ['中国人寿', '国寿', '国寿康宁', '国寿福'],
    '平安': ['平安', '平安福', '平安守护', '平安康逸'],
    '太平洋': ['太平洋', '太保', '金佑人生', '安行宝'],
    '新华': ['新华', '新华保险', '健康福星', '多倍保'],
    '泰康': ['泰康', '泰康人寿', '健康百分百', '乐康宝'],
    '人保': ['人保', '人保寿', '人保健康'],
    '太平': ['太平', '太平人寿', '福禄康逸', '福佑金生'],
    '友邦': ['友邦', '全佑', '传世安赢'],
    '华夏': ['华夏', '华夏保险', '大富翁', '常青树', '菩提'],
    '信泰': ['信泰', '锦绣传承', '如意享', '恒泰连年'],
    '横琴': ['横琴', '传世壹号', '横琴人寿'],
    '爱心': ['爱心', '守护神', '爱心人寿'],
    '中意': ['中意', '悦享', '一生保'],
    '工银安盛': ['工银安盛', '御立方', '御享人生'],
    '光大永明': ['光大永明', '吉瑞宝', '童佳保'],
    '都会': ['都会', '都会臻爱', '都会赢家', '都会臻传'],
    '和谐健康': ['和谐健康', '和谐健康保险'],
}

def detect_insurance_company(text: str) -> str:
    """识别保险公司"""
    if not text:
        return ''
    for company, keywords in INSURANCE_COMPANIES.items():
        for keyword in keywords:
            if keyword in text:
                return company
    return ''

def extract_amount_from_text(text: str) -> Tuple[str, str]:
    """从文本中提取保额/保费金额"""
    if not text:
        return '', ''
    
    # 保额模式：X万、X万元、X千
    amount_pattern = r'([\d,]+(?:\.\d+)?)\s*(万|千|元)'
    matches = re.findall(amount_pattern, str(text))
    
    if matches:
        amount = ''
        for num, unit in matches:
            if unit == '万':
                amount = f"{num}万"
            elif unit == '千':
                amount = f"{num}千"
            elif unit == '元':
                if float(num.replace(',', '')) > 1000:
                    amount = f"{num}元"
        return amount, ''
    
    # 纯数字金额
    num_pattern = r'([\d,]+(?:\.\d+)?)'
    nums = re.findall(num_pattern, str(text))
    if nums and float(nums[0].replace(',', '')) > 0:
        return nums[0], ''
    
    return '', ''

def parse_label_value_row(row: List[Any]) -> Dict[str, str]:
    """解析一行"标签：值"格式的数据"""
    result = {}
    
    if not row or len(row) < 2:
        return result
    
    # 将行数据转换为字符串
    row_str = [str(cell).strip() if pd.notna(cell) else '' for cell in row]
    
    i = 0
    while i < len(row_str) - 1:
        label = row_str[i]
        value = row_str[i + 1] if i + 1 < len(row_str) else ''
        
        # 检查是否是标签（以冒号结尾）
        if label.endswith('：') or label.endswith(':'):
            # 去掉末尾冒号
            label_name = label[:-1].strip()
            
            # 跳过空值
            if value and value != 'nan' and value != '':
                # 特殊字段处理
                if '单号' in label_name:
                    result['保单号'] = value
                elif '状态' in label_name:
                    result['保单状态'] = value
                elif '渠道' in label_name:
                    result['销售渠道'] = value
                elif '频率' in label_name:
                    result['交费频率'] = value
                elif '保费' in label_name:
                    if '期交' in label_name:
                        result['期交保费'] = value
                    elif '累计' in label_name:
                        result['累计保费'] = value
                    else:
                        result['保费'] = value
                elif '生效' in label_name or '承保' in label_name or '受理' in label_name:
                    date_key = '保单生效日期' if '生效' in label_name else ('保单承保日期' if '承保' in label_name else '保单受理日期')
                    result[date_key] = value
                elif '公司' in label_name:
                    result['保险公司'] = value
                    # 同时识别保险公司名
                    detected = detect_insurance_company(value)
                    if detected:
                        result['保险公司识别'] = detected
                elif '产品' in label_name or '险种' in label_name:
                    result['产品名称'] = value
                    # 识别保险公司
                    detected = detect_insurance_company(value)
                    if detected:
                        result['保险公司识别'] = detected
                elif '投保人' in label_name:
                    result['投保人'] = value
                elif '被保人' in label_name or '被保险人' in label_name:
                    result['被保人'] = value
                elif '受益人' in label_name:
                    result['受益人'] = value
                elif '年龄' in label_name:
                    result['年龄'] = value
                elif '性别' in label_name:
                    result['性别'] = value
                elif '电话' in label_name or '手机' in label_name:
                    result['联系电话'] = value
                elif '地址' in label_name:
                    result['地址'] = value
                elif '险种' in label_name:
                    result['险种'] = value
                elif '保障' in label_name:
                    result['保障期限'] = value
                elif '年限' in label_name or '期限' in label_name:
                    result['缴费年限'] = value
                elif '开户' in label_name or '账号' in label_name:
                    result['银行账号'] = value
                elif '开户行' in label_name:
                    result['开户行'] = value
                elif '关系' in label_name:
                    result['关系'] = value
                elif '职业' in label_name:
                    result['职业'] = value
                elif '身高' in label_name or '体重' in label_name:
                    result['体征'] = value
                elif '诊断' in label_name or '病史' in label_name:
                    result['健康状况'] = value
                elif '保费' in label_name or '保额' in label_name:
                    amount, _ = extract_amount_from_text(value)
                    if amount:
                        if '保额' in label_name:
                            result['保额'] = amount
                        else:
                            result['保费金额'] = amount
                elif '核保' in label_name:
                    result['核保结论'] = value
                elif '体检' in label_name:
                    result['体检结论'] = value
                else:
                    # 其他标签直接存储
                    result[label_name] = value
        
        i += 2  # 跳到下一个标签
    
    return result

def extract_from_sheet(df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
    """从单个Sheet提取数据"""
    result = {
        'sheet_name': sheet_name,
        'rows': len(df),
        'columns': list(df.columns),
        'policies': [],
        'customers': {}
    }
    
    # 遍历每一行
    for idx, row in df.iterrows():
        row_data = row.tolist()
        parsed = parse_label_value_row(row_data)
        
        # 如果解析出保单号，说明这是一行保单信息
        if '保单号' in parsed:
            policy_info = {
                '保单号': parsed.get('保单号', ''),
                '保单状态': parsed.get('保单状态', ''),
                '销售渠道': parsed.get('销售渠道', ''),
                '交费频率': parsed.get('交费频率', ''),
                '期交保费': str(parsed.get('期交保费', '')),
                '累计保费': str(parsed.get('累计保费', '')),
                '生效日期': parsed.get('保单生效日期', ''),
                '承保日期': parsed.get('保单承保日期', ''),
                '受理日期': parsed.get('保单受理日期', ''),
                '保险公司': parsed.get('保险公司', ''),
                '保险公司识别': parsed.get('保险公司识别', ''),
                '产品名称': parsed.get('产品名称', ''),
                '险种': parsed.get('险种', ''),
                '保额': parsed.get('保额', ''),
                '保费金额': parsed.get('保费金额', ''),
                '保障期限': parsed.get('保障期限', ''),
                '缴费年限': parsed.get('缴费年限', ''),
            }
            # 过滤空值
            policy_info = {k: v for k, v in policy_info.items() if v}
            if policy_info:
                result['policies'].append(policy_info)
        
        # 提取客户基本信息（投保人、被保人）
        if '投保人' in parsed and parsed['投保人']:
            result['customers']['投保人'] = parsed['投保人']
        if '被保人' in parsed and parsed['被保人']:
            result['customers']['被保人'] = parsed['被保人']
        if '联系电话' in parsed and parsed['联系电话']:
            result['customers']['联系电话'] = parsed['联系电话']
        if '地址' in parsed and parsed['地址']:
            result['customers']['地址'] = parsed['地址']
    
    return result

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
    amount_match = re.search(r'([\d,]+)\s*(万|千|元)', filename)
    if amount_match:
        info['保额'] = f"{amount_match.group(1)}{amount_match.group(2)}"
    
    # 年限提取
    year_match = re.search(r'(\d+)\s*年', filename)
    if year_match:
        info['缴费年限'] = f"{year_match.group(1)}年"
    
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
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                sheet_result = extract_from_sheet(df, sheet_name)
                result['sheets'].append(sheet_result)
                
                # 合并保单信息
                result['policies'].extend(sheet_result['policies'])
                
                # 合并客户信息
                result['customers'].update(sheet_result['customers'])
                
            except Exception as e:
                result['sheets'].append({
                    'sheet_name': sheet_name,
                    'error': str(e)
                })
        
        # 从文件名提取信息
        result['filename_info'] = extract_info_from_filename(filepath.name)
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("Excel文档提取工具 v2 - 修复版")
    print("=" * 60)
    
    # 扫描Excel文件
    excel_files = list(INPUT_DIR.rglob('*.xlsx')) + list(INPUT_DIR.rglob('*.xls'))
    excel_files = [f for f in excel_files if '~$' not in str(f)]  # 排除临时文件
    
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
        print(f"[{idx:3d}/{len(excel_files)}] {filepath.name}")
        print(f"         {status} 成功")
        
        if policy_count > 0:
            print(f"         📋 保单: {policy_count} 个")
            for policy in result['policies'][:3]:  # 只显示前3个
                product = policy.get('产品名称', policy.get('险种', '未知'))
                company = policy.get('保险公司识别', policy.get('保险公司', ''))
                amount = policy.get('保额', policy.get('保费金额', ''))
                print(f"            - {company} {product} {amount}")
        
        if result.get('customers'):
            print(f"         👤 客户信息:")
            for key, value in result['customers'].items():
                print(f"            - {key}: {value}")
        
        print()
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r['success'])
    total_policies = sum(len(r.get('policies', [])) for r in results)
    unique_customers = len(set(
        c for r in results 
        for c in r.get('customers', {}).values() 
        if c
    ))
    
    print("=" * 60)
    print("✅ Excel文档提取完成！")
    print()
    print("📊 统计:")
    print(f"   总文件数: {total}")
    print(f"   成功: {success} ✅")
    print(f"   失败: {total - success} ❌")
    print(f"   成功率: {success/total*100:.1f}%")
    print(f"   提取保单: {total_policies} 个")
    print(f"   涉及客户: {unique_customers} 人")
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 文件已保存: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
