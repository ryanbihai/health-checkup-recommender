#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本解析器 - 从md文本中提取信息
基于规则提取 + LLM智能补全
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class TextParser:
    """文本解析器"""
    
    def __init__(self):
        self.trigger_threshold = float(os.getenv('LLM_TRIGGER_THRESHOLD', '0.5'))
        self.min_table_rows = int(os.getenv('LLM_MIN_TABLE_ROWS', '3'))
        
        # 关键词映射
        self.field_keywords = {
            '险种': ['险种', '产品名称', '产品名', '险种名称'],
            '公司': ['保险公司', '公司'],
            '保额': ['保额', '保障额度', '保险金额', '金额'],
            '保费': ['保费', '险种保费', '期交保费', '年缴保费'],
            '期限': ['缴费期限', '保险期间', '保障期限', '期限'],
            '生效日期': ['生效日期', '生效日', '保险起期'],
            '投保人': ['投保人'],
            '被保险人': ['被保险人'],
            '受益人': ['受益人'],
        }
        
        # 关系词
        self.relationship_keywords = {
            '丈夫': ['丈夫', '老公', '爱人'],
            '妻子': ['妻子', '老婆'],
            '儿子': ['儿子'],
            '女儿': ['女儿'],
            '父亲': ['父亲', '爸爸', '爸'],
            '母亲': ['母亲', '妈妈', '妈'],
        }
    
    def parse_markdown_table(self, content: str) -> List[List[str]]:
        """
        解析Markdown表格
        
        Args:
            content: md文本内容
        
        Returns:
            表格数据列表
        """
        lines = content.split('\n')
        tables = []
        current_table = []
        
        for line in lines:
            line = line.strip()
            if '|' in line and not line.startswith('|---'):
                # 这是一个表格行
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                current_table.append(cells)
            else:
                if current_table:
                    tables.append(current_table)
                    current_table = []
        
        if current_table:
            tables.append(current_table)
        
        return tables
    
    def extract_by_regex(self, content: str) -> Dict[str, Any]:
        """
        使用正则表达式提取信息
        
        Args:
            content: md文本内容
        
        Returns:
            提取的信息字典
        """
        result = {}
        
        # 手机号
        phones = re.findall(r'1[3-9]\d{9}', content)
        if phones:
            result['手机号'] = list(set(phones))
        
        # 身份证号
        id_cards = re.findall(r'\d{17}[\dXx]', content)
        if id_cards:
            result['身份证号'] = list(set([id.upper() for id in id_cards]))
        
        # 日期
        dates = re.findall(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', content)
        if dates:
            result['日期'] = list(set(dates))
        
        # 出生日期（可能在人名后）
        birth_dates = re.findall(r'([^\s]{2,4})\s*([12]\d{3}[-/年]\d{1,2}[-/月]\d{1,2})', content)
        if birth_dates:
            result['可能的出生日期'] = list(set(birth_dates))
        
        # 金额（万）
        amounts = re.findall(r'(\d+(?:\.\d+)?)\s*[万MWmw]', content)
        if amounts:
            result['金额_万'] = [float(a) for a in amounts]
        
        # 性别（从称呼判断）
        if '女士' in content:
            result['性别'] = '女'
        elif '先生' in content:
            result['性别'] = '男'
        
        # 姓名（从文件名或标题提取）
        name_pattern = r'敬致[：:\s]+([^\n]+?)(女士|先生)'
        names = re.findall(name_pattern, content)
        if names:
            result['姓名_敬称'] = [n[0] for n in names]
        
        return result
    
    def extract_from_table(self, table: List[List[str]]) -> Dict[str, Any]:
        """
        从表格中提取信息
        
        Args:
            table: 表格数据
        
        Returns:
            提取的信息
        """
        result = {
            '险种': [],
            '保额': [],
            '保费': [],
            '公司': [],
        }
        
        # 查找标题行
        header_row = 0
        for idx, row in enumerate(table[:5]):
            row_text = ' '.join([str(c) for c in row])
            if any(kw in row_text for kw in ['险种', '保额', '保费', '公司']):
                header_row = idx
                break
        
        # 提取列索引
        header = table[header_row] if header_row < len(table) else []
        col_map = {}
        for col_idx, col_name in enumerate(header):
            col_name = str(col_name).strip()
            for field, keywords in self.field_keywords.items():
                if any(kw in col_name for kw in keywords):
                    col_map[field] = col_idx
                    break
        
        # 提取数据行
        for row in table[header_row + 1:]:
            for field, col_idx in col_map.items():
                if col_idx < len(row):
                    value = str(row[col_idx]).strip()
                    if value and value not in ['nan', '', 'None']:
                        if field in result:
                            if isinstance(result[field], list):
                                result[field].append(value)
        
        return result
    
    def extract_family_members(self, content: str) -> List[Dict[str, str]]:
        """
        提取家庭成员信息
        
        Args:
            content: md文本内容
        
        Returns:
            家庭成员列表
        """
        members = []
        
        # 模式1：从表格列名提取
        table = self.parse_markdown_table(content)
        for t in table:
            for row in t:
                row_text = ' '.join([str(c) for c in row])
                if '被保险人' in row_text:
                    # 这行可能是被保险人信息
                    for cell in row:
                        cell = str(cell).strip()
                        # 查找可能的人名（2-4个汉字）
                        names = re.findall(r'([\u4e00-\u9fa5]{2,4})', cell)
                        for name in names:
                            if name not in ['被保险人', '投保人', '受益人', '险种']:
                                members.append({
                                    '姓名': name,
                                    '关系': '待确认',
                                    '来源': '表格列'
                                })
        
        # 模式2：从文本中识别人名+日期组合（可能是出生日期）
        pattern = r'([\u4e00-\u9fa5]{2,4})\s*([12]\d{3}[-/年]\d{1,2})'
        matches = re.findall(pattern, content)
        for name, date in matches:
            if name not in ['保险', '公司', '产品']:
                members.append({
                    '姓名': name,
                    '出生日期': date,
                    '关系': '待确认',
                    '来源': '文本推断'
                })
        
        # 模式3：从关系词推断
        for relation, keywords in self.relationship_keywords.items():
            for kw in keywords:
                pattern = rf'{kw}\s*：?\s*([\u4e00-\u9fa5]{{2,4}})'
                matches = re.findall(pattern, content)
                for name in matches:
                    members.append({
                        '姓名': name,
                        '关系': relation,
                        '来源': f'关系词"{kw}"'
                    })
        
        # 去重
        seen = set()
        unique_members = []
        for m in members:
            key = m['姓名']
            if key not in seen:
                seen.add(key)
                unique_members.append(m)
        
        return unique_members
    
    def should_trigger_llm(self, extracted_info: Dict[str, Any], content: str) -> tuple[bool, str]:
        """
        判断是否应该触发LLM提取
        
        Args:
            extracted_info: 规则提取的信息
            content: 原始文本
        
        Returns:
            (是否触发, 原因)
        """
        reasons = []
        
        # 条件1：表格行数少
        tables = self.parse_markdown_table(content)
        if tables:
            total_rows = sum(len(t) for t in tables)
            if total_rows < self.min_table_rows:
                reasons.append(f'表格行数少({total_rows}<{self.min_table_rows})')
        
        # 条件2：关键字段缺失
        essential_fields = ['姓名', '险种']
        for field in essential_fields:
            if field not in extracted_info or not extracted_info[field]:
                reasons.append(f'关键字段缺失({field})')
        
        # 条件3：文本包含复杂关系
        complex_keywords = ['家庭', '成员', '配偶', '子女', '健康', '核保', '病史']
        if any(kw in content for kw in complex_keywords):
            reasons.append('包含复杂关系/健康信息')
        
        # 条件4：内容长度适中但规则提取结果少
        if len(content) > 1000 and len(extracted_info) < 3:
            reasons.append('内容丰富但提取结果少')
        
        should_trigger = len(reasons) > 0
        reason = '; '.join(reasons) if reasons else '无需LLM'
        
        return should_trigger, reason
    
    def rule_extract(self, content: str, filename: str) -> Dict[str, Any]:
        """
        规则提取主方法
        
        Args:
            content: md文本内容
            filename: 文件名
        
        Returns:
            提取的信息
        """
        result = {
            '文件名': filename,
            '提取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 1. 正则提取
        regex_info = self.extract_by_regex(content)
        result.update(regex_info)
        
        # 2. 表格提取
        tables = self.parse_markdown_table(content)
        if tables:
            result['表格数量'] = len(tables)
            table_info = self.extract_from_table(tables[0])
            for key, value in table_info.items():
                if key in result:
                    if isinstance(result[key], list):
                        result[key].extend(value)
                else:
                    result[key] = value
        else:
            result['表格数量'] = 0
        
        # 3. 家庭成员
        family_members = self.extract_family_members(content)
        if family_members:
            result['家庭成员'] = family_members
        
        # 4. 文件类型判断
        if '**工作表**' in content:
            result['文件类型'] = 'Excel'
        elif '**页数**' in content:
            result['文件类型'] = 'PDF'
        elif '**幻灯片**' in content:
            result['文件类型'] = 'PPTX'
        elif '**源文件**' in content and '.docx' in content:
            result['文件类型'] = 'DOCX'
        elif '**文件类型: 图片**' in content:
            result['文件类型'] = '图片'
        else:
            result['文件类型'] = '未知'
        
        return result


def test_parser():
    """测试解析器"""
    parser = TextParser()
    
    # 测试内容
    test_content = """
# 龙超影保单利益概要表-20240613
**工作表**: 家庭保障需求分析及规划

## 数据表格

| 姓名 | 险种 | 保额 | 保费 |
| --- | --- | --- | --- |
| 龙超影 | 都会赢家 | 50万 | 2万 |
| 叶文君 | 重疾险 | 30万 | 5000 |
"""
    
    result = parser.rule_extract(test_content, '龙超影保单利益表.md')
    print("规则提取结果：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    should_trigger, reason = parser.should_trigger_llm(result, test_content)
    print(f"\n是否触发LLM: {should_trigger}")
    print(f"原因: {reason}")


if __name__ == '__main__':
    test_parser()
