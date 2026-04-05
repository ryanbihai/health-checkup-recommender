#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档扫描脚本
扫描所有待整理档案文件夹，生成文档清单
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import re

# 路径配置
BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
PENDING_DIR = BASE_DIR / '待整理档案'
OUTPUT_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '文档清单.json'
QUEUE_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '待处理队列.json'
STATS_FILE = BASE_DIR / '客户档案整理项目' / '中间数据' / '扫描统计.json'

def clean_filename(filename: str) -> str:
    """清理文件名"""
    return filename.strip()

def get_file_type(filename: str) -> str:
    """获取文件类型"""
    ext = Path(filename).suffix.lower()
    type_map = {
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.pdf': 'pdf',
        '.pptx': 'powerpoint',
        '.ppt': 'powerpoint',
        '.docx': 'word',
        '.doc': 'word',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.png': 'image',
        '.gif': 'image',
    }
    return type_map.get(ext, 'other')

def guess_document_category(filename: str) -> str:
    """猜测文档类别"""
    filename_lower = filename.lower()
    
    if '保单' in filename or '保单利益' in filename or '概要' in filename:
        return '保单资料'
    elif '保障方案' in filename or '保障规划' in filename:
        return '保障方案'
    elif '产品解析' in filename or '产品说明' in filename:
        return '产品解析'
    elif '比较' in filename or '对比' in filename:
        return '方案比较'
    elif '电子保单' in filename:
        return '电子保单'
    elif '身份证' in filename or '签名' in filename or '证件' in filename:
        return '身份证明'
    elif '方案' in filename or '计划' in filename:
        return '保障方案'
    elif '说明' in filename or '记录' in filename or '备注' in filename:
        return '说明文档'
    else:
        return '其他'

def scan_directory(directory: Path) -> Dict:
    """扫描单个客户目录"""
    result = {
        'client_name': directory.name,
        'client_path': str(directory.relative_to(BASE_DIR)),
        'scan_time': datetime.now().isoformat(),
        'total_files': 0,
        'total_size': 0,
        'documents': []
    }
    
    if not directory.exists():
        return result
    
    # 递归扫描所有文件
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = Path(root) / filename
            
            # 跳过临时文件
            if filename.startswith('~$') or filename.startswith('.'):
                continue
            
            try:
                stat = filepath.stat()
                file_info = {
                    'filename': clean_filename(filename),
                    'filepath': str(filepath.relative_to(BASE_DIR)),
                    'file_type': get_file_type(filename),
                    'file_category': guess_document_category(filename),
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / 1024 / 1024, 2),
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
                
                result['documents'].append(file_info)
                result['total_files'] += 1
                result['total_size'] += stat.st_size
                
            except Exception as e:
                print(f"  ⚠️ 处理文件失败: {filepath} - {e}")
    
    result['total_size_mb'] = round(result['total_size'] / 1024 / 1024, 2)
    
    return result

def main():
    """主函数"""
    print("=" * 60)
    print("文档扫描工具")
    print("=" * 60)
    
    # 确保输出目录存在
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 扫描待整理档案
    print(f"\n📂 正在扫描: {PENDING_DIR}")
    
    if not PENDING_DIR.exists():
        print(f"❌ 目录不存在: {PENDING_DIR}")
        return
    
    all_documents = []
    client_list = []
    file_type_stats = {}
    file_category_stats = {}
    
    # 扫描每个客户目录
    for i, client_dir in enumerate(sorted(PENDING_DIR.iterdir()), 1):
        if not client_dir.is_dir():
            continue
        
        print(f"\n[{i:3d}] 扫描: {client_dir.name}...")
        
        result = scan_directory(client_dir)
        
        if result['total_files'] > 0:
            client_list.append({
                'client_name': result['client_name'],
                'client_path': result['client_path'],
                'total_files': result['total_files'],
                'total_size_mb': result['total_size_mb']
            })
            
            all_documents.append(result)
            
            # 统计文件类型
            for doc in result['documents']:
                file_type = doc['file_type']
                file_type_stats[file_type] = file_type_stats.get(file_type, 0) + 1
                
                file_category = doc['file_category']
                file_category_stats[file_category] = file_category_stats.get(file_category, 0) + 1
    
    # 生成统计信息
    stats = {
        'scan_time': datetime.now().isoformat(),
        'total_clients': len(client_list),
        'total_documents': sum(c['total_files'] for c in client_list),
        'total_size_mb': round(sum(c['total_files'] for c in client_list) / 1024 / 1024, 2),
        'file_type_stats': dict(sorted(file_type_stats.items(), key=lambda x: x[1], reverse=True)),
        'file_category_stats': dict(sorted(file_category_stats.items(), key=lambda x: x[1], reverse=True)),
        'top_clients': sorted(client_list, key=lambda x: x['total_files'], reverse=True)[:20],
    }
    
    # 生成待处理队列（按文档数量排序）
    queue = sorted(client_list, key=lambda x: x['total_files'], reverse=True)
    
    # 保存结果
    print(f"\n\n💾 保存文档清单...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_documents, f, ensure_ascii=False, indent=2)
    
    print(f"💾 保存待处理队列...")
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)
    
    print(f"💾 保存扫描统计...")
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    # 打印统计信息
    print("\n" + "=" * 60)
    print("✅ 扫描完成！")
    print("=" * 60)
    
    print(f"\n📊 统计信息:")
    print(f"   客户总数: {stats['total_clients']}")
    print(f"   文档总数: {stats['total_documents']}")
    print(f"   总大小: {stats['total_size_mb']} MB")
    
    print(f"\n📄 文件类型统计:")
    for file_type, count in stats['file_type_stats'].items():
        print(f"   {file_type:12s}: {count:4d} 个")
    
    print(f"\n📁 文档类别统计:")
    for category, count in stats['file_category_stats'].items():
        print(f"   {category:12s}: {count:4d} 个")
    
    print(f"\n🏆 文档最多的客户 (Top 10):")
    for i, client in enumerate(stats['top_clients'][:10], 1):
        print(f"   {i:2d}. {client['client_name']:20s} - {client['total_files']:3d} 个文档")
    
    print(f"\n💾 文件已保存:")
    print(f"   - 文档清单: {OUTPUT_FILE}")
    print(f"   - 待处理队列: {QUEUE_FILE}")
    print(f"   - 扫描统计: {STATS_FILE}")

if __name__ == '__main__':
    main()
