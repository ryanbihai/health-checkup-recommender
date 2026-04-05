#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文档提取脚本 v2 - 增强版
从PDF文本中解析结构化的保单信息
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

import fitz

# 路径配置
BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
INPUT_DIR = BASE_DIR / '待整理档案'
OUTPUT_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据' / 'pdf_extraction_v2_results.json'
SUMMARY_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据' / 'pdf_customer_summary_v2.json'

def extract_client_info_from_text(text: str) -> Dict[str, Any]:
    """从PDF文本中提取客户信息"""
    info = {
        'client_name': '',
        'gender': '',
        'phone': '',
        'address': ''
    }
    
    # 从"敬致：XXX女士/先生"提取姓名和性别
    gender_pattern = r'敬致[：:]\s*\n?([^\n]+?(?:女士|先生))'
    gender_match = re.search(gender_pattern, text)
    if gender_match:
        name_gender = gender_match.group(1).strip()
        if '女士' in name_gender:
            info['gender'] = '女'
            info['client_name'] = name_gender.replace('女士', '').strip()
        elif '先生' in name_gender:
            info['gender'] = '男'
            info['client_name'] = name_gender.replace('先生', '').strip()
    
    # 从"手  机："提取手机号
    phone_pattern = r'手\s*机[：:]\s*(\d{11})'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        info['phone'] = phone_match.group(1)
    
    # 从公司地址提取地址
    address_pattern = r'公司地址[：:]\s*\n?([^\n]+)'
    address_match = re.search(address_pattern, text)
    if address_match:
        info['address'] = address_match.group(1).strip().replace('\n', ' ')
    
    return info

def extract_policy_info_from_text(text: str) -> List[Dict[str, str]]:
    """从PDF文本中提取保单信息"""
    policies = []
    
    # 提取保险金额模式
    amount_pattern = r'保险金额[（(]单位[：:]\s*人民币[）)]\s*\n?\s*([^\n]+?)\s*\n?\s*([\d,]+(?:\.\d+)?)\s*元'
    amount_matches = re.findall(amount_pattern, text)
    
    for product_name, amount in amount_matches:
        policy = {
            '产品名称': product_name.strip(),
            '保额': amount.strip(),
            '保险公司': '中美联泰大都会人寿'
        }
        policies.append(policy)
    
    # 如果没有找到保险金额，尝试其他模式
    if not policies:
        # 尝试提取产品名称列表
        products = []
        product_patterns = [
            r'都会臻爱终身寿险',
            r'都会赢家[^\n]*',
            r'都会臻传[^\n]*',
            r'守护神[^\n]*',
            r'锦绣传承[^\n]*',
            r'传世壹号[^\n]*',
            r'大富翁[^\n]*',
        ]
        
        for pattern in product_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                product_name = match.strip()
                if product_name and product_name not in products:
                    products.append(product_name)
        
        for product in products:
            policy = {
                '产品名称': product,
                '保额': '',
                '保险公司': '中美联泰大都会人寿'
            }
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
    if '大都会' in filename or '都会' in filename:
        info['保险公司'] = '中美联泰大都会人寿'
    elif '信泰' in filename:
        info['保险公司'] = '信泰保险'
    elif '华夏' in filename:
        info['保险公司'] = '华夏保险'
    elif '横琴' in filename:
        info['保险公司'] = '横琴人寿'
    elif '爱心' in filename:
        info['保险公司'] = '爱心保险'
    elif '和谐' in filename:
        info['保险公司'] = '和谐健康'
    
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
        r'都会臻爱[^\s]*',
        r'都会赢家[^\s]*',
        r'都会臻传[^\s]*',
        r'守护神[^\s]*',
        r'锦绣传承[^\s]*',
        r'传世壹号[^\s]*',
        r'大富翁[^\s]*',
    ]
    
    for pattern in product_patterns:
        product_match = re.search(pattern, filename)
        if product_match:
            info['产品名称'] = product_match.group(0)
            break
    
    return info

def process_pdf_file(filepath: Path) -> Dict[str, Any]:
    """处理单个PDF文件"""
    result = {
        'filepath': str(filepath),
        'filename': filepath.name,
        'file_type': 'pdf',
        'extract_time': datetime.now().isoformat(),
        'success': False,
        'text': '',
        'client_name': '',
        'gender': '',
        'contacts': [],
        'addresses': [],
        'policies': [],
        'filename_info': {}
    }
    
    try:
        doc = fitz.open(filepath)
        text_parts = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            text_parts.append(f"=== 第{page_num + 1}页 ===\n{text}")
        
        result['text'] = '\n\n'.join(text_parts)
        result['page_count'] = len(doc)
        doc.close()
        
        # 提取客户信息
        client_info = extract_client_info_from_text(result['text'])
        result['client_name'] = client_info['client_name']
        result['gender'] = client_info['gender']
        
        if client_info['phone']:
            result['contacts'].append(client_info['phone'])
        
        if client_info['address']:
            result['addresses'].append(client_info['address'])
        
        # 提取保单信息
        text_policies = extract_policy_info_from_text(result['text'])
        result['policies'].extend(text_policies)
        
        # 从文件名提取信息
        filename_info = extract_info_from_filename(filepath.name)
        result['filename_info'] = filename_info
        
        # 如果文件名中有保额但文本中没有，添加文件名中的保额信息
        if filename_info['保额'] and not any(p.get('保额') for p in result['policies']):
            if result['policies']:
                result['policies'][0]['保额'] = filename_info['保额']
            else:
                result['policies'].append({
                    '产品名称': filename_info.get('产品名称', ''),
                    '保额': filename_info['保额'],
                    '保险公司': filename_info['保险公司']
                })
        
        if filename_info['缴费年限']:
            if result['policies']:
                result['policies'][0]['缴费年限'] = filename_info['缴费年限']
        
        # 生成摘要
        result['summary'] = f"文档类型: 保单资料\n客户姓名: {result['client_name']}\n涉及产品: {', '.join([p.get('产品名称', '') for p in result['policies'][:2]])}"
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("PDF文档提取工具 v2 - 增强版")
    print("=" * 60)
    
    # 扫描PDF文件
    pdf_files = list(INPUT_DIR.rglob('*.pdf'))
    pdf_files = [f for f in pdf_files if '~$' not in str(f)]
    
    print(f"\n📂 扫描目录: {INPUT_DIR}")
    print(f"找到 {len(pdf_files)} 个PDF文件\n")
    print("📊 开始提取...\n")
    
    results = []
    customer_data = {}
    
    for idx, filepath in enumerate(pdf_files, 1):
        result = process_pdf_file(filepath)
        results.append(result)
        
        # 按客户文件夹组织数据
        folder_name = filepath.parent.name
        if folder_name not in customer_data:
            customer_data[folder_name] = {
                'folder': folder_name,
                'documents': [],
                'all_contacts': [],
                'all_addresses': [],
                'all_policies': [],
                'client_name': '',
                'gender': ''
            }
        
        customer_data[folder_name]['documents'].append({
            'filename': filepath.name,
            'success': result['success'],
            'policies': result.get('policies', [])
        })
        
        if result.get('contacts'):
            customer_data[folder_name]['all_contacts'].extend(result['contacts'])
        
        if result.get('addresses'):
            customer_data[folder_name]['all_addresses'].extend(result['addresses'])
        
        if result.get('policies'):
            customer_data[folder_name]['all_policies'].extend(result['policies'])
        
        if result.get('client_name'):
            customer_data[folder_name]['client_name'] = result['client_name']
        
        if result.get('gender'):
            customer_data[folder_name]['gender'] = result['gender']
        
        status = "✅" if result['success'] else "❌"
        print(f"[{idx:3d}/{len(pdf_files)}] {filepath.name}")
        print(f"         {status} 成功")
        
        if result.get('client_name'):
            print(f"         👤 客户: {result['client_name']} ({result.get('gender', '')})")
        
        if result.get('contacts'):
            print(f"         📱 手机: {', '.join(result['contacts'])}")
        
        if result.get('policies'):
            print(f"         📋 保单: {len(result['policies'])} 个")
            for policy in result['policies'][:2]:
                print(f"            - {policy.get('产品名称', '')} {policy.get('保额', '')}")
        
        print()
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r['success'])
    
    # 去重联系人
    for folder in customer_data.values():
        folder['all_contacts'] = list(set(folder['all_contacts']))
        folder['all_addresses'] = list(set(folder['all_addresses']))
        
        # 保单去重
        seen = set()
        unique_policies = []
        for policy in folder['all_policies']:
            policy_key = f"{policy.get('产品名称', '')}_{policy.get('保额', '')}"
            if policy_key not in seen:
                seen.add(policy_key)
                unique_policies.append(policy)
        folder['all_policies'] = unique_policies
    
    total_policies = sum(len(c['all_policies']) for c in customer_data.values())
    total_contacts = sum(1 for c in customer_data.values() if c['all_contacts'])
    
    print("=" * 60)
    print("✅ PDF文档提取完成！")
    print()
    print("📊 统计:")
    print(f"   总文件数: {total}")
    print(f"   成功: {success} ✅")
    print(f"   失败: {total - success} ❌")
    print(f"   成功率: {success/total*100:.1f}%")
    print(f"   涉及客户: {len(customer_data)} 个")
    print(f"   提取保单: {total_policies} 个")
    print(f"   有联系方式: {total_contacts} 个")
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(customer_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 文件已保存:")
    print(f"   - 详细结果: {OUTPUT_FILE}")
    print(f"   - 客户汇总: {SUMMARY_FILE}")

if __name__ == '__main__':
    main()
