#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Word文档（RTF/DOCX）提取脚本
从Word文档中提取关键信息
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 路径配置
BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
INPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据'
OUTPUT_FILE = INPUT_DIR / 'doc_extraction_results.json'

def extract_rtf_text(filepath: Path) -> str:
    """从RTF文件提取文本"""
    try:
        # 读取RTF文件
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 移除RTF格式标签
        text = re.sub(r'\\\{|\}|<[^>]+>', ' ', content)
        text = re.sub(r'\\[a-z]+\d+\s', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    except Exception as e:
        return ""

def extract_docx_text(filepath: Path) -> str:
    """从DOCX文件提取文本"""
    try:
        from docx import Document
        doc = Document(str(filepath))
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        return '\n'.join(paragraphs)
    except ImportError:
        return ""
    except Exception as e:
        return ""

def extract_info_from_filename(filename: str) -> Dict:
    """从文件名提取保单信息"""
    info = {
        '保险公司': '',
        '产品名': '',
        '保额': '',
        '缴费年限': '',
        '来源文件名': filename
    }
    
    # 保险公司识别
    company_patterns = [
        (r'信泰', '信泰保险'),
        (r'华夏', '华夏保险'),
        (r'横琴', '横琴人寿'),
        (r'爱心', '爱心保险'),
        (r'都会', '中美联泰大都会'),
        (r'安联', '京东安联'),
        (r'好医保', '好医保'),
        (r'臻传', '中美联泰大都会'),
        (r'臻享', '中美联泰大都会'),
        (r'赢家', '中美联泰大都会'),
        (r'颐年', '中美联泰大都会'),
    ]
    
    for pattern, company in company_patterns:
        if pattern in filename:
            info['保险公司'] = company
            break
    
    # 产品名提取
    product_patterns = [
        r'锦绣传承终身寿',
        r'传世壹号',
        r'大富翁增额版',
        r'守护神[\d\.]+终身寿',
        r'赢家增额终身寿',
        r'颐年[\u4e00-\u9fa5]+',
        r'臻传[\u4e00-\u9fa5]+',
        r'臻享[\u4e00-\u9fa5]+',
        r'常青[\u4e00-\u9fa5]+',
    ]
    
    for pattern in product_patterns:
        match = re.search(pattern, filename)
        if match:
            info['产品名'] = match.group(0)
            break
    
    # 保额提取
    amount_patterns = [
        r'(\d+)万',
        r'(\d+)MW',
        r'(\d+)W',
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, filename)
        if match:
            info['保额'] = f"{match.group(1)}万"
            break
    
    # 缴费年限提取
    year_patterns = [
        r'(\d+)年',
        r'趸(\d+)',
        r'趸交',
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, filename)
        if match:
            if '趸' in pattern and '趸交' in filename:
                info['缴费年限'] = '趸交'
            else:
                info['缴费年限'] = f"{match.group(1)}年"
            break
    
    return info

def extract_info_from_text(text: str, filename: str) -> Dict:
    """从文档内容提取关键信息"""
    info = {
        '手机号': '',
        '姓名': '',
        '地址': '',
        '文档摘要': ''
    }
    
    if not text:
        return info
    
    # 提取手机号
    phone_patterns = [
        r'1[3-9]\d{9}',
        r'\d{3}[-\s]?\d{4}[-\s]?\d{4}',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(0).replace('-', '').replace(' ', '')
            if len(phone) == 11:
                info['手机号'] = phone
                break
    
    # 提取姓名（从文件名或内容）
    name_patterns = [
        r'敬致[：:\s]+([^\s\n]{2,5})(女士|先生)',
        r'投保人[：:\s]+([^\s\n]{2,5})',
        r'被保人[：:\s]+([^\s\n]{2,5})',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) >= 2:
                info['姓名'] = match.group(1)
            else:
                info['姓名'] = match.group(1)
            break
    
    # 生成文档摘要（取前200字符）
    info['文档摘要'] = text[:200].replace('\n', ' ').strip()
    
    return info

def extract_doc(filepath: Path) -> Dict:
    """提取单个Word文档"""
    result = {
        'filepath': str(filepath.relative_to(BASE_DIR)),
        'filename': filepath.name,
        'file_type': 'rtf' if filepath.suffix.lower() == '.doc' else 'docx',
        'extract_time': datetime.now().isoformat(),
        'success': False,
        'text': '',
        'file_info': {},
        'content_info': {}
    }
    
    try:
        # 提取文本内容
        if filepath.suffix.lower() == '.doc':
            result['text'] = extract_rtf_text(filepath)
        elif filepath.suffix.lower() == '.docx':
            result['text'] = extract_docx_text(filepath)
        
        # 从文件名提取保单信息
        result['file_info'] = extract_info_from_filename(filepath.name)
        
        # 从内容提取关键信息
        result['content_info'] = extract_info_from_text(result['text'], filepath.name)
        
        result['success'] = bool(result['text'])
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("Word文档（RTF/DOCX）提取工具")
    print("=" * 60)
    
    # 确保输出目录存在
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 扫描所有Word文档
    pending_dir = BASE_DIR / '待整理档案'
    
    if not pending_dir.exists():
        print(f"❌ 目录不存在: {pending_dir}")
        return
    
    print(f"\n📂 扫描: {pending_dir}")
    
    # 查找所有Word文档
    doc_files = []
    for pattern in ['**/*.doc', '**/*.docx']:
        doc_files.extend(pending_dir.glob(pattern))
    
    print(f"\n找到 {len(doc_files)} 个Word文档")
    
    # 提取每个文档
    results = []
    success_count = 0
    error_count = 0
    
    print(f"\n📊 开始提取...")
    for i, filepath in enumerate(doc_files, 1):
        print(f"\n[{i:3d}/{len(doc_files)}] {filepath.name[:40]}")
        
        result = extract_doc(filepath)
        
        if result['success']:
            success_count += 1
            print(f"         ✅ 成功")
            if result['file_info'].get('产品名'):
                print(f"         📋 产品: {result['file_info']['产品名']}")
            if result['file_info'].get('保额'):
                print(f"         💰 保额: {result['file_info']['保额']}")
            if result['file_info'].get('缴费年限'):
                print(f"         📅 年限: {result['file_info']['缴费年限']}")
            if result['content_info'].get('手机号'):
                print(f"         📱 手机: {result['content_info']['手机号']}")
        else:
            error_count += 1
            print(f"         ❌ 失败: {result.get('error', '未知错误')}")
        
        results.append(result)
    
    # 保存结果
    print(f"\n\n💾 保存结果...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成客户汇总
    client_summary = {}
    for result in results:
        if result['success']:
            # 从文件夹名提取客户
            filepath = result['filepath']
            parts = filepath.split('\\')
            if len(parts) >= 2:
                folder_name = parts[1]  # "待整理档案\\客户名\\文件.doc"
                
                if folder_name not in client_summary:
                    client_summary[folder_name] = {
                        '文件夹': folder_name,
                        '文档数': 0,
                        '保单列表': [],
                        '手机号': '',
                        '文档列表': []
                    }
                
                client_summary[folder_name]['文档数'] += 1
                
                if result['file_info'].get('产品名'):
                    policy = {
                        '产品名': result['file_info']['产品名'],
                        '保额': result['file_info'].get('保额', ''),
                        '缴费年限': result['file_info'].get('缴费年限', ''),
                        '保险公司': result['file_info'].get('保险公司', ''),
                        '来源文件': result['filename']
                    }
                    client_summary[folder_name]['保单列表'].append(policy)
                
                if result['content_info'].get('手机号') and not client_summary[folder_name]['手机号']:
                    client_summary[folder_name]['手机号'] = result['content_info']['手机号']
                
                client_summary[folder_name]['文档列表'].append(result['filename'])
    
    summary_file = INPUT_DIR / 'doc_customer_summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(client_summary, f, ensure_ascii=False, indent=2)
    
    # 打印统计
    print("\n" + "=" * 60)
    print("✅ Word文档提取完成！")
    print("=" * 60)
    
    print(f"\n📊 统计:")
    print(f"   总文件数: {len(doc_files)}")
    print(f"   成功: {success_count} ✅")
    print(f"   失败: {error_count} ❌")
    print(f"   成功率: {success_count/len(doc_files)*100:.1f}%")
    
    print(f"\n🏆 客户统计:")
    for client_name, data in list(client_summary.items())[:10]:
        print(f"   {client_name:20s} - {data['文档数']:2d} 文档, {len(data['保单列表']):2d} 保单")
    
    print(f"\n💾 文件已保存:")
    print(f"   - 提取结果: {OUTPUT_FILE}")
    print(f"   - 客户汇总: {summary_file}")

if __name__ == '__main__':
    main()
