#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案最终整合工具
将 wiki_customers 和 整理后客户md文件 整合为最终档案

输出结构：
- 客户基础信息（来自 wiki_customers/index.md）
- 完整保单明细（来自 整理后客户md文件）
- 数据来源追踪
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict


BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
WIKI_CUSTOMERS_DIR = BASE_DIR / 'wiki_customers' / 'customers'
MD_PROFILES_DIR = BASE_DIR / '整理后客户md文件'
OUTPUT_DIR = BASE_DIR / '整合后客户档案'
OUTPUT_DIR.mkdir(exist_ok=True)


class CustomerProfileMerger:
    def __init__(self):
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'sources': defaultdict(int)
        }
    
    def scan_wiki_customers(self) -> Dict[str, Dict]:
        """扫描wiki_customers目录，获取所有客户基本信息"""
        customers = {}
        
        for customer_dir in WIKI_CUSTOMERS_DIR.iterdir():
            if not customer_dir.is_dir() or customer_dir.name.startswith('.'):
                continue
            
            index_file = customer_dir / 'index.md'
            if index_file.exists():
                try:
                    content = index_file.read_text(encoding='utf-8')
                    basic_info = self._parse_wiki_index(content)
                    basic_info['_source'] = 'wiki_customers'
                    basic_info['_source_path'] = str(index_file)
                    customers[customer_dir.name] = basic_info
                except Exception as e:
                    print(f"   解析wiki索引失败 {customer_dir.name}: {e}")
        
        return customers
    
    def _parse_wiki_index(self, content: str) -> Dict:
        """解析wiki_customers的index.md"""
        info = {
            '姓名': None,
            '性别': None,
            '年龄': None,
            '城市': None,
            '职业': None,
            '联系电话': None,
            '家庭地址': None,
            '邮箱': None,
            '婚姻状况': None,
            '子女情况': None,
            '兴趣爱好': None,
            '特殊需求': None,
            '个人标签': [],
            '家庭成员': []
        }
        
        lines = content.split('\n')
        
        in_personal_info = False
        in_family = False
        
        for i, line in enumerate(lines):
            if '## 个人信息' in line:
                in_personal_info = True
                in_family = False
                continue
            elif '## 个人标签' in line:
                in_personal_info = False
                continue
            elif '## 家庭成员' in line:
                in_personal_info = False
                in_family = True
                continue
            elif line.startswith('## '):
                in_personal_info = False
                in_family = False
            
            if in_personal_info and '|' in line and '---' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    field = parts[1].strip()
                    value = parts[2].strip()
                    
                    field_mapping = {
                        '姓名': '姓名',
                        '性别': '性别',
                        '年龄/生日': '年龄',
                        '城市': '城市',
                        '职业': '职业',
                        '联系电话': '联系电话',
                        '家庭地址': '家庭地址',
                        '邮箱': '邮箱',
                        '婚姻状况': '婚姻状况',
                        '子女情况': '子女情况',
                        '兴趣爱好': '兴趣爱好',
                        '特殊需求': '特殊需求'
                    }
                    
                    if field in field_mapping and value and value not in ['待补充', '待确认', '-', '']:
                        info[field_mapping[field]] = value
            
            if in_family and '|' in line and '---' not in line and '成员' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    member_name = parts[1].strip()
                    relation = parts[2].strip()
                    if member_name and member_name not in ['-', '成员']:
                        info['家庭成员'].append({
                            '姓名': member_name,
                            '关系': relation
                        })
        
        tags = re.findall(r'#(\w+)', content)
        info['个人标签'] = tags
        
        return info
    
    def scan_md_profiles(self) -> Dict[str, Dict]:
        """扫描整理后客户md文件目录"""
        profiles = {}
        
        for md_file in MD_PROFILES_DIR.glob('*.md'):
            if md_file.name == 'profiles_summary.json':
                continue
            
            customer_name = md_file.stem
            try:
                content = md_file.read_text(encoding='utf-8')
                profile_info = self._parse_md_profile(content)
                profile_info['_source'] = '整理后客户md文件'
                profile_info['_source_path'] = str(md_file)
                profiles[customer_name] = profile_info
            except Exception as e:
                print(f"   解析md档案失败 {customer_name}: {e}")
        
        return profiles
    
    def _parse_md_profile(self, content: str) -> Dict:
        """解析整理后客户md文件"""
        info = {
            '基本信息': {},
            '保单列表': [],
            '其他地址': []
        }
        
        lines = content.split('\n')
        current_section = None
        current_policy = {}
        in_basic_info = False
        in_policies = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if stripped.startswith('## 基本信息'):
                in_basic_info = True
                in_policies = False
                continue
            elif stripped.startswith('## 保单信息'):
                in_basic_info = False
                in_policies = True
                current_policy = {}
                continue
            elif stripped.startswith('## 其他地址'):
                in_basic_info = False
                in_policies = False
                continue
            elif stripped.startswith('## ') and not in_policies:
                in_basic_info = False
                in_policies = False
            
            if in_basic_info and stripped.startswith('- **'):
                match = re.match(r'- \*\*(.*?)\*\*:\s*(.*)', stripped)
                if match:
                    field = match.group(1)
                    value = match.group(2).strip()
                    info['基本信息'][field] = value
            
            if in_policies:
                if stripped.startswith('### 保单'):
                    if current_policy:
                        info['保单列表'].append(current_policy)
                    current_policy = {}
                elif stripped.startswith('- **'):
                    match = re.match(r'- \*\*(.*?)\*\*:\s*(.*)', stripped)
                    if match:
                        field = match.group(1)
                        value = match.group(2).strip()
                        current_policy[field] = value
                elif stripped.startswith('*来源*') or stripped.startswith('- *来源*'):
                    match = re.search(r'\*来源\*:\s*(.*)', stripped)
                    if match:
                        current_policy['数据来源'] = match.group(1).strip()
        
        if current_policy:
            info['保单列表'].append(current_policy)
        
        for line in lines:
            if '**地址**' in line or '**联系地址**' in line:
                addr_match = re.search(r'\*?(来源)?:\s*(.*)', line)
                if addr_match:
                    addr = addr_match.group(2).strip().rstrip('*')
                    if addr and '来源' not in addr:
                        info['其他地址'].append(addr)
        
        return info
    
    def find_matching_profiles(self, wiki_customers: Dict, md_profiles: Dict) -> List[tuple]:
        """匹配两个来源的客户档案"""
        matches = []
        
        all_names = set(wiki_customers.keys()) | set(md_profiles.keys())
        
        for name in all_names:
            wiki = wiki_customers.get(name)
            md = md_profiles.get(name)
            
            if wiki and md:
                matches.append((name, wiki, md, 'both'))
                self.stats['sources']['both'] += 1
            elif wiki:
                matches.append((name, wiki, None, 'wiki_only'))
                self.stats['sources']['wiki_only'] += 1
            elif md:
                matches.append((name, None, md, 'md_only'))
                self.stats['sources']['md_only'] += 1
        
        return matches
    
    def merge_profiles(self, name: str, wiki_info: Optional[Dict], md_info: Optional[Dict], match_type: str) -> str:
        """合并两个来源的客户档案"""
        now = datetime.now().strftime('%Y-%m-%d')
        
        content = f"""# {name}

> 创建时间：{now}
> 数据来源：{'wiki_customers + 整理后客户md文件' if match_type == 'both' else ('wiki_customers' if match_type == 'wiki_only' else '整理后客户md文件')}

---

## 基本信息

"""
        
        basic_info = {}
        sources = []
        
        if wiki_info:
            sources.append(wiki_info.get('_source_path', 'wiki_customers'))
            for key, value in wiki_info.items():
                if key.startswith('_'):
                    continue
                if value and value not in ['待补充', '待确认', '-', '']:
                    if key == '个人标签' and isinstance(value, list):
                        basic_info['个人标签'] = value
                    elif key == '家庭成员' and isinstance(value, list):
                        basic_info['家庭成员'] = value
                    elif value:
                        basic_info[key] = value
        
        if md_info:
            sources.append(md_info.get('_source_path', '整理后客户md文件'))
            md_basic = md_info.get('基本信息', {})
            for key, value in md_basic.items():
                if value and value not in ['待补充', '待确认', '-', '']:
                    basic_info[key] = value
            
            md_addresses = md_info.get('其他地址', [])
            if md_addresses:
                basic_info['其他地址'] = md_addresses
        
        field_order = [
            '姓名', '性别', '年龄', '出生日期', '手机号', '联系电话',
            '微信号', '邮箱', '身份证号', '住址', '地址', '职业',
            '工作单位', '年收入', '婚姻状况', '与投保人关系',
            '兴趣爱好', '特殊需求', '个人标签', '家庭成员', '其他地址'
        ]
        
        for field in field_order:
            if field == '个人标签' and '个人标签' in basic_info:
                tags = basic_info['个人标签']
                if tags:
                    content += f"- **个人标签**: {', '.join(tags)}\n"
            elif field == '家庭成员' and '家庭成员' in basic_info:
                members = basic_info['家庭成员']
                if members:
                    content += "\n### 家庭成员\n\n"
                    content += "| 姓名 | 关系 |\n"
                    content += "|------|------|\n"
                    for m in members:
                        if isinstance(m, dict):
                            content += f"| {m.get('姓名', '')} | {m.get('关系', '')} |\n"
                        else:
                            content += f"| {m} | |\n"
            elif field == '其他地址' and '其他地址' in basic_info:
                addrs = basic_info['其他地址']
                if addrs:
                    content += "\n### 其他地址\n\n"
                    for addr in addrs:
                        content += f"- {addr}\n"
            elif field in basic_info and basic_info[field]:
                value = basic_info[field]
                if isinstance(value, str) and value:
                    content += f"- **{field}**: {value}\n"
        
        content += "\n---\n\n## 保单信息\n\n"
        
        policies = []
        if md_info:
            policies = md_info.get('保单列表', [])
        
        if policies:
            policy_num = 1
            for policy in policies:
                if not policy or not policy.get('产品名称'):
                    continue
                
                if policy.get('产品名称', '').strip() in ['暂无保单信息', '']:
                    continue
                
                content += f"### 保单 {policy_num}\n\n"
                
                policy_fields = [
                    ('保险公司', '保险公司'),
                    ('保单号', '保单号'),
                    ('投保人', '投保人'),
                    ('被保险人', '被保人', '被保险人'),
                    ('受益人', '受益人'),
                    ('产品名称', '产品名称'),
                    ('险种', '险种'),
                    ('保额', '保额'),
                    ('保费', '保费', '年缴保费'),
                    ('保险期间', '保险期间'),
                    ('缴费年限', '缴费年限'),
                    ('生效日期', '生效日期'),
                    ('犹豫期', '犹豫期'),
                    ('宽限期', '宽限期'),
                    ('等待期', '等待期'),
                    ('生存金', '生存金'),
                    ('满期金', '满期金'),
                    ('身故保险金', '身故保险金'),
                    ('现金价值', '现金价值'),
                    ('核保结论', '核保结论'),
                    ('特别约定', '特别约定'),
                ]
                
                for field_def in policy_fields:
                    if len(field_def) == 2:
                        display_name, key = field_def
                    else:
                        display_name, key, alt_key = field_def
                        key = key if key in policy else alt_key
                    
                    if key in policy and policy[key]:
                        value = str(policy[key]).strip()
                        if value and value not in ['-', '', '无', '暂无']:
                            content += f"- **{display_name}**: {value}\n"
                
                if '数据来源' in policy:
                    content += f"- *来源*: {policy['数据来源']}\n"
                
                content += "\n"
                policy_num += 1
        else:
            content += "*暂无保单信息*\n\n"
        
        content += "---\n\n## 数据来源\n\n"
        for src in sources:
            src_name = Path(src).name if src else '未知'
            content += f"- {src_name}: `{src}`\n"
        
        content += f"\n---\n*最后更新: {now}*\n"
        
        return content
    
    def process_all(self):
        """处理所有客户档案"""
        print("=" * 60)
        print("客户档案整合工具")
        print("=" * 60)
        
        print("\n📂 扫描 wiki_customers...")
        wiki_customers = self.scan_wiki_customers()
        print(f"   找到 {len(wiki_customers)} 个客户档案")
        
        print("\n📂 扫描 整理后客户md文件...")
        md_profiles = self.scan_md_profiles()
        print(f"   找到 {len(md_profiles)} 个客户档案")
        
        print("\n🔗 匹配客户档案...")
        matches = self.find_matching_profiles(wiki_customers, md_profiles)
        self.stats['total'] = len(matches)
        print(f"   总计 {len(matches)} 个客户")
        
        both_count = sum(1 for _, _, _, t in matches if t == 'both')
        wiki_only = sum(1 for _, _, _, t in matches if t == 'wiki_only')
        md_only = sum(1 for _, _, _, t in matches if t == 'md_only')
        print(f"   - 两边都有: {both_count}")
        print(f"   - 仅 wiki_customers: {wiki_only}")
        print(f"   - 仅 整理后客户md文件: {md_only}")
        
        print("\n" + "=" * 60)
        print("开始整合...")
        print("=" * 60)
        
        for i, (name, wiki_info, md_info, match_type) in enumerate(matches, 1):
            print(f"\n[{i}/{len(matches)}] 整合客户：{name}")
            print(f"   来源: {match_type}")
            
            try:
                content = self.merge_profiles(name, wiki_info, md_info, match_type)
                
                safe_name = name.replace('/', '-').replace('\\', '-')
                output_file = OUTPUT_DIR / f"{safe_name}.md"
                output_file.write_text(content, encoding='utf-8')
                
                print(f"   ✅ 已保存: {output_file.name}")
                self.stats['success'] += 1
            except Exception as e:
                print(f"   ❌ 失败: {e}")
                self.stats['failed'] += 1
        
        self._print_summary()
    
    def _print_summary(self):
        """打印统计摘要"""
        print("\n" + "=" * 60)
        print("整合完成！")
        print("=" * 60)
        print(f"\n📊 统计：")
        print(f"   总客户数：{self.stats['total']}")
        print(f"   成功：{self.stats['success']} ✅")
        print(f"   失败：{self.stats['failed']} ❌")
        print(f"\n📁 数据来源分布：")
        for src, count in sorted(self.stats['sources'].items()):
            src_name = {
                'both': '两边都有',
                'wiki_only': '仅 wiki_customers',
                'md_only': '仅 整理后客户md文件'
            }.get(src, src)
            print(f"   - {src_name}: {count}")
        print(f"\n📁 输出目录：{OUTPUT_DIR}")


def main():
    merger = CustomerProfileMerger()
    merger.process_all()


if __name__ == '__main__':
    main()
