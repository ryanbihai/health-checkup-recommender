#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析各类源文件的信息字段
"""

import os
import sys
from pathlib import Path

# 读取docx文件
def read_docx(file_path):
    """读取docx文件内容"""
    try:
        from docx import Document
        doc = Document(file_path)
        content = []
        for para in doc.paragraphs:
            if para.text.strip():
                content.append(para.text)
        return '\n'.join(content)
    except Exception as e:
        return f"Error: {str(e)}"

# 读取Excel文件
def read_excel_fields(file_path):
    """读取Excel文件的列名"""
    try:
        import pandas as pd
        df = pd.read_excel(file_path, header=None, nrows=5)
        first_row = df.iloc[0].tolist() if len(df) > 0 else []
        return [str(v) for v in first_row if str(v) != 'nan']
    except Exception as e:
        return [f"Error: {str(e)}"]

def main():
    base_dir = Path(r'待整理档案')
    
    print("=" * 80)
    print("各类文件信息字段分析")
    print("=" * 80)
    
    # 1. 分析Excel文件
    print("\n\n## 1. Excel文件字段分析\n")
    excel_files = [
        "黄葵/黄葵保单利益表-2025.xlsx",
        "黄常青/许露尹-20万5年都会赢家_全数据.xlsx",
        "高丽丽-罗冠/罗冠家庭保单利益表20250222_高丽丽.xlsx",
        "李泽华/张洋/张洋-都会赢家10万10年.xlsx",
        "刘文杰/刘文杰保单利益说明-202501.xlsx",
    ]
    
    for file_path in excel_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"\n文件: {file_path}")
            fields = read_excel_fields(full_path)
            print(f"列名: {fields}")

    # 2. 分析docx文件
    print("\n\n## 2. Word文档内容分析\n")
    docx_files = [
        "高丽丽-罗冠/已有保单的几点情况说明.docx",
        "曲颖/情况说明.docx",
        "郭宇飞-路越/郭宇飞体检报告可能核保结论.docx",
        "岳晨/岳晨 情况 说明.docx",
        "叶结明/保险情况.docx",
        "好啦/深轻/深轻科技团险报价20220424.docx",
    ]
    
    for file_path in docx_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"\n文件: {file_path}")
            content = read_docx(full_path)
            print(f"内容预览:\n{content[:500]}...")
    
    # 3. 分析PDF内容摘要
    print("\n\n## 3. PDF文件内容摘要\n")
    print("""
根据已转换的MD文件分析，PDF文件包含以下关键信息：
- 客户姓名、性别
- 出生日期、年龄
- 险种名称、保险类型（主约/附约）
- 保险期间、保险金额（单位：人民币）
- 保费明细、交费类型
- 被保险人信息、投保人信息
- 保障说明、保单利益
- 生存金、满期金、身故保险金
- 保单年度、现金价值
- 犹豫期、宽限期说明
""")

    # 4. 分析PPTX内容摘要
    print("\n## 4. PowerPoint文件内容摘要\n")
    print("""
根据已转换的MD文件分析，PPTX文件包含以下关键信息：
- 产品名称、产品特色
- 保障方案、保障额度
- 缴费期限、领取方式
- 利益演示、收益分析
- 产品对比、产品亮点
- 适用人群、销售话术
- 方案解析、客户需求分析
""")

    # 5. 分析图片文件
    print("\n## 5. 图片文件类型\n")
    print("""
根据文件命名分析，图片文件包含以下类型：
- 身份证照片（例：文稚清新身份证-1.jpg）
- 签字扫描件（例：邝美森签字.jpg）
- 保单截图（例：旧保单-任娜/*.jpg）
- 微信聊天截图（例：微信图片_*.jpg）
- 产品截图（例：小公主保障.jpg）
- 其他证明材料
""")

if __name__ == '__main__':
    main()
