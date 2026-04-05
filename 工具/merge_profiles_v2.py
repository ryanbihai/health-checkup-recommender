#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案合并脚本 v2.0
从PDF文本中提取关键信息，正确填入MD档案
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# 路径配置
BASE_DIR = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具')
INPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据'
OUTPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '合并数据_v2'

class EnhancedMerger:
    """增强版客户档案合并器"""
    
    def __init__(self):
        self.pdf_data = []
        self.excel_data = []
        self.processed_clients = {}
        
    def load_data(self):
        """加载所有数据"""
        print("📖 加载数据...")
        
        # 加载PDF提取结果
        pdf_file = INPUT_DIR / 'pdf_pptx_extraction_results.json'
        if pdf_file.exists():
            with open(pdf_file, 'r', encoding='utf-8') as f:
                self.pdf_data = json.load(f)
            print(f"   - PDF/PPTX数据: {len(self.pdf_data)} 条")
        
        # 加载Excel提取结果
        excel_file = INPUT_DIR / 'excel_extraction_results.json'
        if excel_file.exists():
            with open(excel_file, 'r', encoding='utf-8') as f:
                self.excel_data = json.load(f)
            print(f"   - Excel数据: {len(self.excel_data)} 条")
    
    def extract_info_from_text(self, text: str, filename: str) -> Dict:
        """从PDF文本中提取关键信息"""
        info = {
            '手机号': '',
            '性别': '',
            '地址': '',
            '敬致人': '',  # PDF中"敬致："后面的人名
            '保单列表': []
        }
        
        # 1. 提取手机号
        phone_patterns = [
            r'手\s*机[：:]\s*([0-9-]{11,})',
            r'手机[：:]\s*([0-9-]{11,})',
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(1).strip().replace('-', '')
                if len(phone) >= 11:
                    info['手机号'] = phone
                    break
        
        # 2. 提取性别（从"敬致：XXX女士/先生"）
        gender_patterns = [
            r'敬致[：:\s]+([^\n]{0,5})(女士|先生)',
            r'敬致[：:\s]+([^\n]{0,5})(女士|先生)',
        ]
        for pattern in gender_patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                gender = match.group(2)
                if name and len(name) >= 2:
                    info['敬致人'] = name
                    info['性别'] = '女' if gender == '女士' else '男'
                    break
        
        # 3. 提取地址
        addr_patterns = [
            r'公司地址[：:]\s*([^\n]{5,60})',
            r'地址[：:]\s*([^\n]{5,60})',
        ]
        for pattern in addr_patterns:
            match = re.search(pattern, text)
            if match:
                addr = match.group(1).strip().replace(' ', '')
                if len(addr) >= 5:
                    info['地址'] = addr[:50]  # 截断过长的地址
                    break
        
        # 4. 从文件名提取保单信息
        policy = self.extract_policy_from_filename(filename)
        if policy:
            info['保单列表'].append(policy)
        
        return info
    
    def extract_policy_from_filename(self, filename: str) -> Dict:
        """从文件名提取保单信息"""
        policy = {
            '产品名': '',
            '保额': '',
            '年缴': '',
            '来源文件': filename
        }
        
        # 提取产品名
        product_patterns = [
            r'都会[\u4e00-\u9fa5]+',
            r'安鑫[\u4e00-\u9fa5]+',
            r'赢家[\u4e00-\u9fa5]+',
            r'康逸[\u4e00-\u9fa5]+',
            r'臻享[\u4e00-\u9fa5]+',
            r'颐年[\u4e00-\u9fa5]+',
            r'常青[\u4e00-\u9fa5]+',
        ]
        for pattern in product_patterns:
            match = re.search(pattern, filename)
            if match:
                policy['产品名'] = match.group(0)
                break
        
        # 提取保额（数字+万/M）
        amount_patterns = [
            r'(\d+)万',
            r'(\d+)MW',
            r'(\d+)M',
            r'(\d+)W',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, filename)
            if match:
                amount = match.group(1)
                # 判断是保额还是年缴
                if '年缴' in filename or '趸' in filename or '10年' in filename or '20年' in filename:
                    policy['年缴'] = f'{amount}万'
                else:
                    policy['保额'] = f'{amount}万'
                break
        
        # 如果没有提取到任何信息，返回空
        if not policy['产品名'] and not policy['保额']:
            return None
        
        return policy
    
    def extract_info_from_excel(self, item: Dict) -> Dict:
        """从Excel中提取信息"""
        info = {
            '投保人': '',
            '被保人': '',
            '手机号': '',
            '保单列表': []
        }
        
        if not item.get('sheets'):
            return info
        
        # 遍历所有sheet
        for sheet in item['sheets']:
            if not sheet.get('data'):
                continue
            
            # 遍历每一行
            for row_data in sheet['data']:
                row_str = str(row_data)
                
                # 查找投保人
                if '投保人' in row_str or '投保人姓名' in row_str:
                    # 尝试提取姓名
                    name_match = re.search(r'投保人[：:]\s*([^\s,，]+)', str(row_data))
                    if name_match:
                        info['投保人'] = name_match.group(1)
                
                # 查找被保人
                if '被保人' in row_str or '被保险人' in row_str:
                    name_match = re.search(r'被[保]?人[：:]\s*([^\s,，]+)', str(row_data))
                    if name_match:
                        info['被保人'] = name_match.group(1)
                
                # 查找手机号
                phone_match = re.search(r'1[3-9]\d{9}', str(row_data))
                if phone_match and not info['手机号']:
                    info['手机号'] = phone_match.group(0)
        
        return info
    
    def process_all(self):
        """处理所有数据"""
        print("\n🔄 开始处理数据...")
        
        # 按文件夹分组PDF数据
        folder_data = defaultdict(list)
        
        for pdf_item in self.pdf_data:
            filepath = pdf_item.get('filepath', '')
            # 提取文件夹名
            parts = filepath.split('\\')
            if len(parts) >= 2:
                folder_name = parts[1]  # "待整理档案\XXX\文件.pdf"
            else:
                folder_name = '未知'
            
            folder_data[folder_name].append(pdf_item)
        
        # 处理每个文件夹
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        processed_count = 0
        
        for folder_name, pdf_items in folder_data.items():
            if folder_name == '未知' or not folder_name:
                continue
            
            # 创建客户档案
            client_profile = self.create_client_profile(folder_name, pdf_items)
            
            if client_profile:
                # 保存档案
                safe_name = re.sub(r'[<>:"/\\|?*]', '', folder_name)
                output_file = OUTPUT_DIR / f'客户_{safe_name}.md'
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(client_profile)
                
                processed_count += 1
                
                if processed_count % 20 == 0:
                    print(f"   已处理: {processed_count} 个客户")
        
        return processed_count
    
    def create_client_profile(self, folder_name: str, pdf_items: List[Dict]) -> str:
        """创建客户档案"""
        
        # 基本信息
        basic_info = {
            '姓名': folder_name,
            '性别': '',
            '出生日期': '待确认',
            '年龄': '待确认',
            '手机号': '',
            '邮箱': '待补充',
            '身份证号': '待补充',
            '住址': '',
            '职业': '待确认'
        }
        
        # 家庭成员
        family_members = []
        
        # 保单列表
        policy_list = []
        
        # 处理每个PDF文件
        all_info = {
            '手机号': [],
            '性别': [],
            '地址': [],
            '敬致人': set()
        }
        
        for pdf_item in pdf_items:
            text = pdf_item.get('text', '')
            filename = pdf_item.get('filename', '')
            
            # 从文本提取信息
            info = self.extract_info_from_text(text, filename)
            
            # 收集信息
            if info['手机号']:
                all_info['手机号'].append(info['手机号'])
            if info['性别']:
                all_info['性别'].append(info['性别'])
            if info['地址']:
                all_info['地址'].append(info['地址'])
            if info['敬致人']:
                all_info['敬致人'].add(info['敬致人'])
            
            # 收集保单
            for policy in info['保单列表']:
                if policy:
                    policy['来源文件'] = filename
                    policy_list.append(policy)
        
        # 填充基本信息（取第一个非空值）
        if all_info['手机号']:
            basic_info['手机号'] = all_info['手机号'][0]
        if all_info['性别']:
            basic_info['性别'] = all_info['性别'][0]
        if all_info['地址']:
            basic_info['住址'] = all_info['地址'][0]
        
        # 如果没有性别但有敬致人，从敬致人提取
        if not basic_info['性别'] and all_info['敬致人']:
            first_person = list(all_info['敬致人'])[0]
            # 检查是否是家属（与文件夹名不同）
            if first_person != folder_name and len(first_person) >= 2:
                family_members.append({
                    '关系': '待确认',
                    '姓名': first_person,
                    '备注': '从PDF中识别'
                })
        
        # 处理家庭成员（如果文件夹名包含"-"，则拆分）
        if '-' in folder_name:
            parts = folder_name.split('-')
            if len(parts) >= 2:
                basic_info['姓名'] = parts[0]  # 第一个人作为主客户
                for part in parts[1:]:
                    if len(part) >= 2:
                        family_members.append({
                            '关系': '家属',
                            '姓名': part,
                            '备注': '从文件夹名识别'
                        })
        
        # 生成保单信息Markdown
        policy_md = self.generate_policy_md(policy_list)
        
        # 生成家庭成员Markdown
        family_md = self.generate_family_md(family_members)
        
        # 生成文档清单Markdown
        docs_md = self.generate_docs_md(folder_name, pdf_items)
        
        # 组合完整的档案
        profile = f"""# 客户档案：{basic_info['姓名']}

## 基本信息
姓名：{basic_info['姓名']}
性别：{basic_info['性别'] or '待确认'}
出生日期：{basic_info['出生日期']}
年龄：{basic_info['年龄']}
手机号：{basic_info['手机号'] or '待确认'}
邮箱：{basic_info['邮箱']}
身份证号：{basic_info['身份证号']}
住址：{basic_info['住址'] or '待确认'}
职业：{basic_info['职业']}

## 客户状态
客户状态：待确认
来源渠道：待了解
与我关系：直接客户
信任程度：⭐⭐⭐
建档日期：{datetime.now().strftime('%Y-%m-%d')}
最后更新：{datetime.now().strftime('%Y-%m-%d')}

## 家庭成员
{family_md}

## 保单信息
{policy_md}

## 健康信息
体检记录：无
既往病史：无
健康关注：无

## 财务信息
年收入：待评估
主要诉求：待沟通
风险偏好：待了解

## 重要日期
生日：待确认
保单周年：待确认
续费日期：待确认

## 销售机会
待开发

## 互动历史
暂无

{docs_md}

## 数据冲突记录
暂无记录

## 特殊备注
待补充

---
档案创建：{datetime.now().strftime('%Y-%m-%d')} | 从{len(pdf_items)}个文档自动提取
"""
        
        return profile
    
    def generate_policy_md(self, policies: List[Dict]) -> str:
        """生成保单信息Markdown"""
        if not policies:
            return "### 主险\n险种类别：待确认\n保险公司：待确认\n保额：待确认\n生效日期：待确认\n年缴保费：待确认\n保单状态：待确认"
        
        md_parts = []
        
        for i, policy in enumerate(policies, 1):
            md_parts.append(f"### 保单{i}")
            md_parts.append(f"险种名称：{policy.get('产品名', '待确认')}")
            md_parts.append(f"保额：{policy.get('保额', '待确认')}")
            md_parts.append(f"年缴保费：{policy.get('年缴', '待确认')}")
            md_parts.append(f"保险公司：中美联泰大都会人寿")
            md_parts.append(f"保单状态：待确认")
            md_parts.append(f"来源文件：{policy.get('来源文件', 'N/A')}")
            md_parts.append("")
        
        return '\n'.join(md_parts)
    
    def generate_family_md(self, family: List[Dict]) -> str:
        """生成家庭成员Markdown"""
        if not family:
            return "- 无（待补充）"
        
        md_parts = []
        for member in family:
            relation = member.get('关系', '关系待确认')
            name = member.get('姓名', 'N/A')
            note = member.get('备注', '')
            md_parts.append(f"- {relation}：{name}，{note}")
        
        return '\n'.join(md_parts)
    
    def generate_docs_md(self, folder_name: str, pdf_items: List[Dict]) -> str:
        """生成文档清单Markdown"""
        md_parts = ["## 关联文档清单", "### 原始文档"]
        
        for item in pdf_items:
            filename = item.get('filename', 'N/A')
            page_count = item.get('page_count', 'N/A')
            md_parts.append(f"- {folder_name}\\{filename} ({page_count}页)")
        
        md_parts.append("")
        md_parts.append(f"### 数据来源")
        md_parts.append("- PDF文档自动提取")
        
        return '\n'.join(md_parts)

def main():
    """主函数"""
    print("=" * 60)
    print("客户档案合并工具 v2.0")
    print("=" * 60)
    
    merger = EnhancedMerger()
    
    # 加载数据
    merger.load_data()
    
    # 处理所有数据
    count = merger.process_all()
    
    print("\n" + "=" * 60)
    print("✅ 处理完成！")
    print("=" * 60)
    
    print(f"\n📊 统计:")
    print(f"   成功处理客户: {count}")
    print(f"\n💾 输出位置:")
    print(f"   {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
