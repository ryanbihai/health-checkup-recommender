#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案合并脚本 v3 - 整合所有数据源
合并PDF、Word、Excel提取结果，生成完整客户档案
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import defaultdict

# 路径配置
BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
PROJECT_DIR = BASE_DIR / '客户档案整理项目'
EXTRACTED_DATA_DIR = PROJECT_DIR / '中间数据' / '提取数据'
SOURCE_DIR = BASE_DIR / '待整理档案'
OUTPUT_DIR = BASE_DIR / '整理后客户md文件'

# 提取结果文件
PDF_RESULTS_FILE = EXTRACTED_DATA_DIR / 'pdf_customer_summary_v2.json'
WORD_RESULTS_FILE = EXTRACTED_DATA_DIR / 'doc_customer_summary.json'
EXCEL_RESULTS_FILE = EXTRACTED_DATA_DIR / 'excel_extraction_v4_results.json'

def load_json(filepath: Path) -> Any:
    """加载JSON文件"""
    if not filepath.exists():
        print(f"⚠️ 文件不存在: {filepath}")
        return {} if 'customer_summary' in str(filepath) else []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_folder_name(filepath: str) -> str:
    """从文件路径提取文件夹名称"""
    parts = filepath.replace('\\', '/').split('/')
    if len(parts) >= 2:
        return parts[-2]
    return ''

def normalize_phone(phone: str) -> str:
    """规范化手机号"""
    if not phone:
        return ''
    phone = re.sub(r'[^\d]', '', phone)
    if len(phone) == 11 and phone.startswith('1'):
        return phone
    return phone

def extract_name_from_folder(folder_name: str) -> Dict[str, str]:
    """从文件夹名称提取主客户和家属信息"""
    if '-' in folder_name:
        parts = folder_name.split('-')
        main_name = parts[0].strip()
        family_name = '-'.join(parts[1:]).strip()
        return {'main': main_name, 'family': family_name}
    return {'main': folder_name, 'family': ''}

def merge_policy_info(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """合并保单信息，去重"""
    if not existing:
        return new
    if not new:
        return existing
    
    existing_policy_ids = set()
    for policy in existing:
        if '保单号' in policy:
            existing_policy_ids.add(policy['保单号'])
    
    merged = existing.copy()
    for policy in new:
        policy_id = policy.get('保单号', '')
        if policy_id and policy_id not in existing_policy_ids:
            merged.append(policy)
            existing_policy_ids.add(policy_id)
        elif not policy_id:
            merged.append(policy)
    
    return merged

def merge_customer_info(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """合并客户信息"""
    merged = existing.copy()
    for key, value in new.items():
        if key not in merged or not merged[key]:
            merged[key] = value
        elif key == '联系电话' and merged[key] != value:
            if value:
                existing_phones = merged[key].split('/') if '/' in merged[key] else [merged[key]]
                new_phone = normalize_phone(value)
                if new_phone and new_phone not in [normalize_phone(p) for p in existing_phones]:
                    merged[key] = merged[key] + ' / ' + value
        elif key == '地址' and merged[key] != value:
            if value:
                merged[key] = value
    return merged

def process_source_folder(folder_path: Path, pdf_data: Dict, word_data: Dict, excel_data: Dict) -> Dict[str, Any]:
    """处理单个客户文件夹"""
    folder_name = folder_path.name
    
    result = {
        'folder_name': folder_name,
        'extract_time': datetime.now().isoformat(),
        'files_count': 0,
        'file_types': defaultdict(int),
        'customers': {
            'main': {},
            'family': {}
        },
        'policies': [],
        'contacts': [],
        'addresses': []
    }
    
    name_info = extract_name_from_folder(folder_name)
    result['main_customer_name'] = name_info['main']
    result['family_member_name'] = name_info['family']
    
    policies = []
    contacts = []
    addresses = []
    customers = {'main': {}, 'family': {}}
    
    folder_key = folder_name.replace('\\', '/')
    
    if folder_key in word_data:
        word_info = word_data[folder_key]
        
        if word_info.get('保单列表'):
            for policy in word_info['保单列表']:
                policy_record = {
                    '产品名称': policy.get('产品名', ''),
                    '保额': policy.get('保额', ''),
                    '缴费年限': policy.get('缴费年限', ''),
                    '保险公司': policy.get('保险公司', ''),
                    '来源文件': policy.get('来源文件', ''),
                    'source': 'word'
                }
                policies.append(policy_record)
        
        if word_info.get('手机号'):
            contacts.append({'type': 'phone', 'value': word_info['手机号'], 'source': 'word'})
    
    if folder_key in excel_data:
        excel_info = excel_data[folder_key]
        if excel_info.get('customers'):
            for key, value in excel_info['customers'].items():
                if key == '联系电话' and value:
                    contacts.append({'type': 'phone', 'value': value, 'source': 'excel'})
                elif key == '地址' and value:
                    addresses.append({'type': 'address', 'value': value, 'source': 'excel'})
        
        for policy in excel_info.get('policies', []):
            policy['source'] = 'excel'
            policy['source_file'] = excel_info.get('filename', '')
            policies.append(policy)
        
        if excel_info.get('customers', {}).get('投保人'):
            customers['main']['投保人关系'] = excel_info['customers']['投保人']
    
    if folder_key in pdf_data:
        pdf_info = pdf_data[folder_key]
        
        if pdf_info.get('all_contacts'):
            for contact in pdf_info['all_contacts']:
                contacts.append({'type': 'phone', 'value': contact, 'source': 'pdf'})
        
        if pdf_info.get('all_addresses'):
            for addr in pdf_info['all_addresses']:
                addresses.append({'type': 'address', 'value': addr, 'source': 'pdf'})
        
        if pdf_info.get('gender'):
            customers['main']['性别'] = pdf_info['gender']
        
        if pdf_info.get('all_policies'):
            for policy in pdf_info['all_policies']:
                policy_copy = policy.copy()
                policy_copy['source'] = 'pdf'
                policies.append(policy_copy)
    
    for file in folder_path.iterdir():
        if file.is_file():
            result['files_count'] += 1
            ext = file.suffix.lower()
            if ext == '.pdf':
                result['file_types']['pdf'] += 1
            elif ext in ['.doc', '.docx', '.rtf']:
                result['file_types']['word'] += 1
            elif ext in ['.xls', '.xlsx']:
                result['file_types']['excel'] += 1
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                result['file_types']['image'] += 1
            elif ext in ['.ppt', '.pptx']:
                result['file_types']['pptx'] += 1
    
    unique_contacts = []
    seen_contacts = set()
    for contact in contacts:
        normalized = normalize_phone(contact['value'])
        if normalized and normalized not in seen_contacts:
            unique_contacts.append(contact)
            seen_contacts.add(normalized)
    
    unique_addresses = []
    seen_addresses = set()
    for addr in addresses:
        if addr['value'] and addr['value'] not in seen_addresses:
            unique_addresses.append(addr)
            seen_addresses.add(addr['value'])
    
    unique_policies = []
    seen_policy_ids = set()
    for policy in policies:
        policy_id = policy.get('保单号', '')
        if policy_id and policy_id not in seen_policy_ids:
            unique_policies.append(policy)
            seen_policy_ids.add(policy_id)
        elif not policy_id:
            unique_policies.append(policy)
    
    result['contacts'] = unique_contacts
    result['addresses'] = unique_addresses
    result['policies'] = unique_policies
    result['customers'] = customers
    
    return result

def generate_markdown_profile(customer_data: Dict) -> str:
    """生成Markdown格式的客户档案"""
    lines = []
    lines.append(f"# {customer_data['main_customer_name']}")
    lines.append("")
    
    if customer_data['family_member_name']:
        lines.append(f"**家属**: {customer_data['family_member_name']}")
        lines.append("")
    
    lines.append("## 基本信息")
    lines.append("")
    
    main_customer = customer_data.get('customers', {}).get('main', {})
    if main_customer.get('性别'):
        lines.append(f"- **性别**: {main_customer['性别']}")
    
    if main_customer.get('投保人关系'):
        lines.append(f"- **与投保人关系**: {main_customer['投保人关系']}")
    
    if customer_data.get('contacts'):
        lines.append(f"- **联系电话**: {' / '.join([c['value'] for c in customer_data['contacts']])}")
    
    if customer_data.get('addresses'):
        lines.append(f"- **地址**: {customer_data['addresses'][0]['value']}")
    
    lines.append("")
    lines.append("## 保单信息")
    lines.append("")
    
    if customer_data.get('policies'):
        for idx, policy in enumerate(customer_data['policies'], 1):
            lines.append(f"### 保单 {idx}")
            lines.append("")
            for key, value in policy.items():
                if key not in ['source', 'source_file']:
                    lines.append(f"- **{key}**: {value}")
            if policy.get('source'):
                lines.append(f"- *来源*: {policy['source']}文档")
            lines.append("")
    else:
        lines.append("*暂无保单信息*")
        lines.append("")
    
    if customer_data.get('addresses') and len(customer_data['addresses']) > 1:
        lines.append("## 其他地址")
        lines.append("")
        for addr in customer_data['addresses'][1:]:
            lines.append(f"- {addr['value']} ({addr['source']}文档)")
        lines.append("")
    
    lines.append("---")
    lines.append(f"*最后更新: {customer_data['extract_time']}*")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    print("=" * 70)
    print("客户档案合并工具 v3 - 整合所有数据源")
    print("=" * 70)
    
    print("\n📂 加载提取结果...")
    
    pdf_results = load_json(PDF_RESULTS_FILE)
    word_results = load_json(WORD_RESULTS_FILE)
    excel_results = load_json(EXCEL_RESULTS_FILE)
    
    print(f"   PDF数据: {len(pdf_results)} 条记录")
    print(f"   Word数据: {len(word_results)} 条记录")
    print(f"   Excel数据: {len(excel_results)} 条记录")
    
    pdf_data = pdf_results if isinstance(pdf_results, dict) else {}
    
    word_data = word_results if isinstance(word_results, dict) else {}
    
    excel_data = {}
    for item in excel_results:
        folder = extract_folder_name(item.get('filepath', ''))
        if folder:
            excel_data[folder] = item
    
    print(f"\n📊 数据映射:")
    print(f"   PDF客户: {len(pdf_data)} 个")
    print(f"   Word客户: {len(word_data)} 个")
    print(f"   Excel客户: {len(excel_data)} 个")
    
    # 过滤掉无效的文件夹名称
    invalid_folders = ['待整理档案', '', '备份', '__MACOSX']
    pdf_data = {k: v for k, v in pdf_data.items() if k not in invalid_folders}
    word_data = {k: v for k, v in word_data.items() if k not in invalid_folders}
    excel_data = {k: v for k, v in excel_data.items() if k not in invalid_folders}
    
    print("\n📂 扫描源文件夹...")
    folders = [f for f in SOURCE_DIR.iterdir() if f.is_dir() and not f.name.startswith('.')]
    folders = [f for f in folders if f.name not in ['备份', '.backup', '__MACOSX']]
    
    print(f"   找到 {len(folders)} 个客户文件夹")
    
    print("\n🔄 开始合并数据...")
    
    all_profiles = []
    stats = {
        'total_folders': len(folders),
        'with_policies': 0,
        'with_contacts': 0,
        'with_addresses': 0,
        'total_policies': 0
    }
    
    for idx, folder in enumerate(sorted(folders), 1):
        folder_name = folder.name
        
        customer_data = process_source_folder(folder, pdf_data, word_data, excel_data)
        all_profiles.append(customer_data)
        
        if customer_data.get('policies'):
            stats['with_policies'] += 1
            stats['total_policies'] += len(customer_data['policies'])
        
        if customer_data.get('contacts'):
            stats['with_contacts'] += 1
        
        if customer_data.get('addresses'):
            stats['with_addresses'] += 1
        
        progress = (idx / len(folders)) * 100
        print(f"\r[{'=' * int(progress/5):<20}] {idx}/{len(folders)} {folder_name}", end='', flush=True)
    
    print("\n\n" + "=" * 70)
    print("✅ 数据合并完成！")
    print()
    print("📊 统计:")
    print(f"   总文件夹: {stats['total_folders']}")
    print(f"   有保单: {stats['with_policies']} 个 ({stats['with_policies']/stats['total_folders']*100:.1f}%)")
    print(f"   有联系方式: {stats['with_contacts']} 个")
    print(f"   有地址: {stats['with_addresses']} 个")
    print(f"   总保单数: {stats['total_policies']} 条")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    summary_file = OUTPUT_DIR / 'profiles_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_profiles, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 汇总文件已保存: {summary_file}")
    
    print("\n📝 生成Markdown客户档案...")
    
    for idx, customer_data in enumerate(all_profiles, 1):
        folder_name = customer_data['folder_name']
        safe_filename = folder_name.replace('/', '_').replace('\\', '_').replace('*', '_').replace('?', '_')
        md_file = OUTPUT_DIR / f"{safe_filename}.md"
        
        md_content = generate_markdown_profile(customer_data)
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"   [{idx:3d}/{len(all_profiles)}] {folder_name}.md", end='')
        if customer_data.get('policies'):
            print(f" ({len(customer_data['policies'])} 保单)", end='')
        print()
    
    print(f"\n💾 Markdown档案已保存到: {OUTPUT_DIR}")
    print(f"   共 {len(all_profiles)} 个客户档案")

if __name__ == '__main__':
    main()
