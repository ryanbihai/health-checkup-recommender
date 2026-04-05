#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性验证与归档脚本
"""

import os
import json
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具')
PROJECT_DIR = BASE_DIR / '客户档案整理项目'
INPUT_DIR = PROJECT_DIR / '中间数据'
OUTPUT_DIR = PROJECT_DIR / '最终数据'
MERGED_DIR = INPUT_DIR / '合并数据'
LLM_DIR = INPUT_DIR / 'LLM处理数据'

def verify_data():
    """验证数据完整性"""
    print("=" * 60)
    print("数据完整性验证")
    print("=" * 60)
    
    stats = {
        '扫描': {},
        '提取': {},
        '合并': {},
        'LLM处理': {}
    }
    
    # 1. 验证扫描数据
    print("\n📋 1. 验证扫描数据...")
    scan_file = INPUT_DIR / '文档清单.json'
    if scan_file.exists():
        with open(scan_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        stats['扫描']['文档总数'] = sum(d['total_files'] for d in scan_data)
        stats['扫描']['客户文件夹数'] = len(scan_data)
        print(f"   ✅ 文档总数: {stats['扫描']['文档总数']}")
        print(f"   ✅ 客户文件夹: {stats['扫描']['客户文件夹数']}")
    else:
        print(f"   ❌ 扫描文件不存在")
    
    # 2. 验证提取数据
    print("\n📋 2. 验证提取数据...")
    
    excel_results = INPUT_DIR / '提取数据' / 'excel_extraction_results.json'
    if excel_results.exists():
        with open(excel_results, 'r', encoding='utf-8') as f:
            excel_data = json.load(f)
        stats['提取']['Excel成功数'] = sum(1 for d in excel_data if d.get('success'))
        print(f"   ✅ Excel提取成功: {stats['提取']['Excel成功数']}")
    else:
        print(f"   ❌ Excel提取结果不存在")
    
    pdf_results = INPUT_DIR / '提取数据' / 'pdf_pptx_extraction_results.json'
    if pdf_results.exists():
        with open(pdf_results, 'r', encoding='utf-8') as f:
            pdf_data = json.load(f)
        stats['提取']['PDF/PPTX成功数'] = sum(1 for d in pdf_data if d.get('success'))
        print(f"   ✅ PDF/PPTX提取成功: {stats['提取']['PDF/PPTX成功数']}")
    else:
        print(f"   ❌ PDF/PPTX提取结果不存在")
    
    # 3. 验证合并数据
    print("\n📋 3. 验证合并数据...")
    if MERGED_DIR.exists():
        merged_files = list(MERGED_DIR.glob('客户_*.md'))
        stats['合并']['合并档案数'] = len(merged_files)
        print(f"   ✅ 合并客户档案: {stats['合并']['合并档案数']}")
        
        # 检查冲突报告
        conflict_file = MERGED_DIR / '冲突报告.json'
        if conflict_file.exists():
            with open(conflict_file, 'r', encoding='utf-8') as f:
                conflict_data = json.load(f)
            stats['合并']['冲突数'] = conflict_data.get('total_conflicts', 0)
            print(f"   ⚠️ 检测冲突: {stats['合并']['冲突数']}")
        else:
            print(f"   ✅ 无冲突")
    else:
        print(f"   ❌ 合并数据目录不存在")
    
    # 4. 验证LLM处理数据
    print("\n📋 4. 验证LLM处理数据...")
    if LLM_DIR.exists():
        llm_results = LLM_DIR / 'llm_extraction_results.json'
        if llm_results.exists():
            with open(llm_results, 'r', encoding='utf-8') as f:
                llm_data = json.load(f)
            stats['LLM处理']['处理文档数'] = len(llm_data)
            print(f"   ✅ LLM处理文档: {stats['LLM处理']['处理文档数']}")
        
        insights_file = LLM_DIR / 'client_insights.json'
        if insights_file.exists():
            with open(insights_file, 'r', encoding='utf-8') as f:
                insights_data = json.load(f)
            stats['LLM处理']['识别客户数'] = len(insights_data)
            print(f"   ✅ 识别客户: {stats['LLM处理']['识别客户数']}")
    else:
        print(f"   ❌ LLM处理数据目录不存在")
    
    return stats

def generate_final_report(stats: dict):
    """生成最终报告"""
    print("\n" + "=" * 60)
    print("最终统计报告")
    print("=" * 60)
    
    report = f"""# 客户档案整理项目 - 最终报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 项目概述

本项目将待整理档案中的客户资料整理为结构化的Markdown客户档案。

## 数据统计

### 扫描阶段
- 客户文件夹数：{stats.get('扫描', {}).get('客户文件夹数', 'N/A')}
- 文档总数：{stats.get('扫描', {}).get('文档总数', 'N/A')}

### 提取阶段
- Excel提取成功：{stats.get('提取', {}).get('Excel成功数', 'N/A')}
- PDF/PPTX提取成功：{stats.get('提取', {}).get('PDF/PPTX成功数', 'N/A')}

### 合并阶段
- 合并客户档案：{stats.get('合并', {}).get('合并档案数', 'N/A')}
- 检测冲突数：{stats.get('合并', {}).get('冲突数', 'N/A')}

### LLM处理阶段
- LLM处理文档：{stats.get('LLM处理', {}).get('处理文档数', 'N/A')}
- 识别客户数：{stats.get('LLM处理', {}).get('识别客户数', 'N/A')}

## 文件位置

### 中间数据
- 文档清单：`{INPUT_DIR / '文档清单.json'}`
- Excel提取结果：`{INPUT_DIR / '提取数据' / 'excel_extraction_results.json'}`
- PDF/PPTX提取结果：`{INPUT_DIR / '提取数据' / 'pdf_pptx_extraction_results.json'}`
- 合并档案：`{MERGED_DIR}`
- 冲突报告：`{MERGED_DIR / '冲突报告.json'}`
- LLM处理结果：`{LLM_DIR}`

### 原始数据
- 待整理档案：`{BASE_DIR / '待整理档案'}`
- 备份：`{BASE_DIR / '备份'}`

## 使用说明

1. **查看客户档案**：浏览 `{MERGED_DIR}` 目录下的Markdown文件
2. **查看销售洞察**：阅读 `{LLM_DIR / 'sales_insights_report.md'}`
3. **处理冲突**：查阅 `{MERGED_DIR / '冲突报告-可读.md'}`

## 下一步

1. 人工审核合并的客户档案
2. 处理检测到的数据冲突
3. 根据销售洞察制定跟进计划

---
报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUT_DIR / 'final_report.md'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 最终报告已生成: {report_file}")
    
    # 保存统计JSON
    stats_file = OUTPUT_DIR / 'final_stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 统计数据已保存: {stats_file}")
    
    return report

def main():
    """主函数"""
    print("=" * 60)
    print("客户档案整理项目 - 最终阶段")
    print("=" * 60)
    
    # 验证数据
    stats = verify_data()
    
    # 生成报告
    report = generate_final_report(stats)
    
    print("\n" + "=" * 60)
    print("✅ 项目完成！")
    print("=" * 60)
    
    print("\n📁 所有文件位于:")
    print(f"   项目目录: {PROJECT_DIR}")
    print(f"   中间数据: {INPUT_DIR}")
    print(f"   最终报告: {OUTPUT_DIR / 'final_report.md'}")

if __name__ == '__main__':
    main()
