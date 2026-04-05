#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案最终整合工具 v2
整合多个来源的客户信息：
1. wiki_customers
2. 整理后客户md文件
3. 备份/客户档案 (包含生日、性别等完整信息)
4. 备份/客户档案备份
5. 备份/待整理档案md (补充保单信息)

输出：整合后客户档案
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict


BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
WIKI_CUSTOMERS_DIR = BASE_DIR / 'wiki_customers' / 'customers'
MD_PROFILES_DIR = BASE_DIR / '整理后客户md文件'
BACKUP_PROFILES_DIR = BASE_DIR / '备份' / '客户档案'
BACKUP_PROFILES_DIR2 = BASE_DIR / '备份' / '客户档案备份'
UNORGANIZED_DIR = BASE_DIR / '备份' / '待整理档案md'
OUTPUT_DIR = BASE_DIR / '整合后客户档案'
OUTPUT_DIR.mkdir(exist_ok=True)


MALE_NAMES = {
    '毕海', '于剑', '付博', '任艳龙', '何嘉鑫', '侯科峰', '刘冕', '刘剑', '刘坤',
    '刘延生', '刘永锋', '刘金水', '刘金林', '区鹏', '卞俞涵', '史超', '叶红军',
    '叶结明', '吴非', '周召辉', '唐周屹', '姜勇', '孙航', '官建军', '富尧', '崔仂',
    '张勇', '张名洋', '张建志', '张宏涛', '张帆', '张强杨卉', '张恺', '张晶宇',
    '张超', '张跃鸿', '张铭轩', '张鹤', '彭亮锋', '徐冠男', '房少辉', '敖雷雷',
    '朱俊', '朱劲松', '朱志强', '李君元', '李响', '李国栋', '李巍然', '李立',
    '李智勇', '李泽华', '李迪华', '杨冬', '杨磊', '林子乔', '梁宇', '梁宇淳',
    '毕海', '池东津', '汤万荣', '汪学诗', '牛旭东', '牛薪', '王亮', '王健',
    '王兆宁', '王凯', '王家鹏', '王小宝', '王旭', '王武群', '王永庆', '王潇博',
    '王瀚洋', '王琦', '王祎', '王红钢', '王耀', '王鹏飞', '田新', '翟栩超',
    '肖光', '苏俊', '苗蓬威', '范文庆', '裴艳德', '谭元坤', '贾堂', '贾文东',
    '贾晨东', '邓永鹏', '邝美森', '邱传伟', '郑直', '郝恺', '郭宇飞', '阿布',
    '黄强', '黄明彪', '黄金华', '龙超影', '遆广西', '邓必健', '任昊', '黄晓婷'
}


class CustomerProfileMergerV2:
    def __init__(self):
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'new_from_backup': 0,
            'birthday_updated': 0,
            'gender_corrected': 0,
            'sources': defaultdict(int)
        }
        self.existing_profiles = {}
        self.all_customer_names = set()
    
    def load_existing_profiles(self):
        """加载已存在的整合档案"""
        if OUTPUT_DIR.exists():
            for md_file in OUTPUT_DIR.glob('*.md'):
                if md_file.name == 'A保障脑图.md' or md_file.name == '都会颐年方案.md':
                    continue
                name = md_file.stem
                self.existing_profiles[name] = md_file.read_text(encoding='utf-8')
        print(f"   已加载 {len(self.existing_profiles)} 个已存在的档案")
    
    def scan_wiki_customers(self) -> Dict[str, Dict]:
        """扫描wiki_customers目录"""
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
                    self.all_customer_names.add(customer_dir.name)
                except Exception as e:
                    print(f"   解析wiki索引失败 {customer_dir.name}: {e}")
        
        return customers
    
    def _parse_wiki_index(self, content: str) -> Dict:
        """解析wiki_customers的index.md"""
        info = {
            '姓名': None, '性别': None, '年龄': None, '城市': None,
            '职业': None, '联系电话': None, '家庭地址': None, '邮箱': None,
            '婚姻状况': None, '子女情况': None, '兴趣爱好': None,
            '特殊需求': None, '个人标签': [], '家庭成员': []
        }
        
        lines = content.split('\n')
        in_personal_info = False
        in_family = False
        
        for line in lines:
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
                        '姓名': '姓名', '性别': '性别', '年龄/生日': '年龄',
                        '城市': '城市', '职业': '职业', '联系电话': '联系电话',
                        '家庭地址': '家庭地址', '邮箱': '邮箱', '婚姻状况': '婚姻状况',
                        '子女情况': '子女情况', '兴趣爱好': '兴趣爱好', '特殊需求': '特殊需求'
                    }
                    if field in field_mapping and value and value not in ['待补充', '待确认', '-', '']:
                        info[field_mapping[field]] = value
            
            if in_family and '|' in line and '---' not in line and '成员' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    member_name = parts[1].strip()
                    relation = parts[2].strip()
                    if member_name and member_name not in ['-', '成员']:
                        info['家庭成员'].append({'姓名': member_name, '关系': relation})
        
        tags = re.findall(r'#(\w+)', content)
        info['个人标签'] = tags
        
        return info
    
    def scan_md_profiles(self) -> Dict[str, Dict]:
        """扫描整理后客户md文件目录"""
        profiles = {}
        
        for md_file in MD_PROFILES_DIR.glob('*.md'):
            if md_file.name in ['profiles_summary.json', 'A保障脑图.md', '都会颐年方案.md']:
                continue
            
            customer_name = md_file.stem
            try:
                content = md_file.read_text(encoding='utf-8')
                profile_info = self._parse_md_profile(content)
                profile_info['_source'] = '整理后客户md文件'
                profile_info['_source_path'] = str(md_file)
                profiles[customer_name] = profile_info
                self.all_customer_names.add(customer_name)
            except Exception as e:
                print(f"   解析md档案失败 {customer_name}: {e}")
        
        return profiles
    
    def _parse_md_profile(self, content: str) -> Dict:
        """解析整理后客户md文件"""
        info = {'基本信息': {}, '保单列表': [], '其他地址': []}
        
        lines = content.split('\n')
        in_basic_info = False
        in_policies = False
        current_policy = {}
        
        for line in lines:
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
                    info['基本信息'][match.group(1)] = match.group(2).strip()
            
            if in_policies:
                if stripped.startswith('### 保单'):
                    if current_policy:
                        info['保单列表'].append(current_policy)
                    current_policy = {}
                elif stripped.startswith('- **'):
                    match = re.match(r'- \*\*(.*?)\*\*:\s*(.*)', stripped)
                    if match:
                        current_policy[match.group(1)] = match.group(2).strip()
                elif stripped.startswith('*来源*') or stripped.startswith('- *来源*'):
                    match = re.search(r'\*来源\*:\s*(.*)', stripped)
                    if match:
                        current_policy['数据来源'] = match.group(1).strip()
        
        if current_policy:
            info['保单列表'].append(current_policy)
        
        return info
    
    def scan_backup_profiles(self) -> Dict[str, Dict]:
        """扫描备份/客户档案目录"""
        profiles = {}
        
        dirs_to_scan = [BACKUP_PROFILES_DIR, BACKUP_PROFILES_DIR2]
        
        for dir_path in dirs_to_scan:
            if not dir_path.exists():
                continue
            
            for md_file in dir_path.glob('*.md'):
                match = re.match(r'客户档案_(.+)', md_file.name)
                if match:
                    name = match.group(1)
                elif md_file.name.startswith('客户_'):
                    name = md_file.name[3:-3]
                else:
                    continue
                
                try:
                    content = md_file.read_text(encoding='utf-8')
                    info = self._parse_backup_profile(content)
                    info['_source'] = '备份客户档案'
                    info['_source_path'] = str(md_file)
                    profiles[name] = info
                    self.all_customer_names.add(name)
                except Exception as e:
                    print(f"   解析备份档案失败 {md_file.name}: {e}")
        
        return profiles
    
    def _parse_backup_profile(self, content: str) -> Dict:
        """解析备份客户档案格式"""
        info = {
            '出生日期': None, '年龄': None, '手机号': None, '邮箱': None,
            '身份证号': None, '住址': None, '职业': None, '企业': None,
            '客户关系': None, '信任程度': None, '客户类型': None,
            '价值分层': None, '需求类型': None, '风险偏好': None,
            '标签': [], '特殊备注': []
        }
        
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('姓名：'):
                info['姓名'] = stripped[3:].strip()
            elif stripped.startswith('性别：'):
                gender = stripped[3:].strip()
                info['性别'] = gender
            elif stripped.startswith('出生日期：'):
                birthday = stripped[5:].strip().replace("'", "").replace("'", "")
                if birthday and birthday not in ['待确认', '-', '']:
                    info['出生日期'] = birthday
            elif stripped.startswith('年龄：'):
                age = stripped[3:].strip()
                if age and age not in ['待确认', '-', '']:
                    info['年龄'] = age
            elif stripped.startswith('手机号：'):
                phone = stripped[4:].strip().replace("'", "").replace("'", "")
                if phone and phone not in ['待确认', '-', '']:
                    info['手机号'] = phone
            elif stripped.startswith('邮箱：'):
                email = stripped[3:].strip()
                if email and email not in ['待确认', '-', '']:
                    info['邮箱'] = email
            elif stripped.startswith('身份证号：'):
                id_num = stripped[5:].strip().replace("'", "").replace("'", "")
                if id_num and id_num not in ['待确认', '-', '']:
                    info['身份证号'] = id_num
            elif stripped.startswith('住址：'):
                addr = stripped[3:].strip()
                if addr and addr not in ['待确认', '-', '']:
                    info['住址'] = addr
            elif stripped.startswith('职业：'):
                job = stripped[3:].strip()
                if job and job not in ['待确认', '-', '']:
                    info['职业'] = job
            elif '企业:' in stripped:
                match = re.search(r'企业:([^#\s]+)', stripped)
                if match:
                    info['企业'] = match.group(1)
            elif stripped.startswith('#'):
                tags = re.findall(r'#(\w+)', stripped)
                info['标签'].extend(tags)
        
        return info
    
    def scan_unorganized_profiles(self) -> Dict[str, List[Dict]]:
        """扫描备份/待整理档案md目录，提取保单信息"""
        profiles = defaultdict(list)
        
        if not UNORGANIZED_DIR.exists():
            return profiles
        
        for customer_dir in UNORGANIZED_DIR.iterdir():
            if not customer_dir.is_dir():
                continue
            
            customer_name = customer_dir.name
            
            for md_file in customer_dir.glob('*.md'):
                if '_Sheet' in md_file.name or '_分析规划' in md_file.name or '_需求分析' in md_file.name or '_规划' in md_file.name or '_总体规划' in md_file.name:
                    continue
                
                try:
                    content = md_file.read_text(encoding='utf-8')
                    policies = self._extract_policies_from_unorganized(content, md_file.name)
                    if policies:
                        profiles[customer_name].extend(policies)
                        self.all_customer_names.add(customer_name)
                except Exception as e:
                    pass
        
        return profiles
    
    def _extract_policies_from_unorganized(self, content: str, filename: str) -> List[Dict]:
        """从未整理档案中提取保单信息"""
        policies = []
        
        name_match = re.search(r'投保人[:：]\s*([^\n\r]+)', content)
        product_match = re.search(r'产品名称[:：]\s*([^\n\r]+)', content)
        company_match = re.search(r'保险公司[:：]\s*([^\n\r]+)', content)
        
        if name_match and product_match:
            policy = {
                '投保人': name_match.group(1).strip(),
                '产品名称': product_match.group(1).strip(),
                '保险公司': company_match.group(1).strip() if company_match else None,
                '数据来源': filename
            }
            
            amount_match = re.search(r'保险金额[:：]\s*([^\n\r]+)', content)
            if amount_match:
                policy['保额'] = amount_match.group(1).strip()
            
            premium_match = re.search(r'保险费|年缴保费[:：]\s*([^\n\r]+)', content)
            if premium_match:
                policy['保费'] = premium_match.group(1).strip()
            
            period_match = re.search(r'保险期间[:：]\s*([^\n\r]+)', content)
            if period_match:
                policy['保险期间'] = period_match.group(1).strip()
            
            policies.append(policy)
        
        return policies
    
    def find_matching_profiles(self, sources: Dict[str, Dict]) -> List[tuple]:
        """匹配所有来源的客户档案"""
        matches = []
        
        for name in sorted(self.all_customer_names):
            source_data = {}
            for src_name, src_data in sources.items():
                if name in src_data:
                    source_data[src_name] = src_data[name]
            
            if source_data:
                matches.append((name, source_data))
        
        return matches
    
    def _correct_gender(self, name: str, current_gender: Optional[str]) -> str:
        """纠正性别信息"""
        if name in MALE_NAMES:
            return '男'
        elif current_gender:
            return current_gender
        return current_gender or ''
    
    def merge_profiles(self, name: str, source_data: Dict[str, Dict]) -> str:
        """合并多个来源的客户档案"""
        now = datetime.now().strftime('%Y-%m-%d')
        
        info = {
            '姓名': name, '性别': '', '出生日期': '', '年龄': '',
            '手机号': '', '联系电话': '', '邮箱': '', '身份证号': '',
            '住址': '', '地址': '', '职业': '', '企业': '',
            '婚姻状况': '', '与投保人关系': '',
            '个人标签': [], '家庭成员': [],
            '其他地址': [],
            '保单列表': []
        }
        
        sources = []
        
        wiki_info = source_data.get('wiki_customers')
        if wiki_info:
            sources.append(wiki_info.get('_source_path', 'wiki_customers'))
            if wiki_info.get('性别') and wiki_info['性别'] not in ['待补充', '待确认']:
                info['性别'] = wiki_info['性别']
            if wiki_info.get('联系电话') and info['手机号'] == '':
                info['联系电话'] = wiki_info['联系电话']
            if wiki_info.get('家庭地址') and info['住址'] == '':
                info['住址'] = wiki_info['家庭地址']
            if wiki_info.get('职业') and info['职业'] == '':
                info['职业'] = wiki_info['职业']
            if wiki_info.get('婚姻状况') and info['婚姻状况'] == '':
                info['婚姻状况'] = wiki_info['婚姻状况']
            tags = wiki_info.get('个人标签', [])
            if tags:
                info['个人标签'].extend(tags)
            members = wiki_info.get('家庭成员', [])
            if members:
                info['家庭成员'].extend(members)
        
        backup_info = source_data.get('备份客户档案')
        if backup_info:
            sources.append(backup_info.get('_source_path', '备份客户档案'))
            if backup_info.get('出生日期') and info['出生日期'] == '':
                info['出生日期'] = backup_info['出生日期']
                self.stats['birthday_updated'] += 1
            if backup_info.get('年龄') and info['年龄'] == '':
                info['年龄'] = backup_info['年龄']
            if backup_info.get('手机号') and info['手机号'] == '':
                info['手机号'] = backup_info['手机号']
            if backup_info.get('联系电话') and info['联系电话'] == '':
                info['联系电话'] = backup_info['联系电话']
            if backup_info.get('邮箱') and info['邮箱'] == '':
                info['邮箱'] = backup_info['邮箱']
            if backup_info.get('身份证号') and info['身份证号'] == '':
                info['身份证号'] = backup_info['身份证号']
            if backup_info.get('住址') and info['住址'] == '':
                info['住址'] = backup_info['住址']
            if backup_info.get('职业') and info['职业'] == '':
                info['职业'] = backup_info['职业']
            if backup_info.get('企业') and info['企业'] == '':
                info['企业'] = backup_info['企业']
            backup_gender = backup_info.get('性别', '')
            if backup_gender:
                info['性别'] = backup_gender
        
        md_info = source_data.get('整理后客户md文件')
        if md_info:
            sources.append(md_info.get('_source_path', '整理后客户md文件'))
            md_basic = md_info.get('基本信息', {})
            if md_basic.get('性别') and info['性别'] == '':
                info['性别'] = md_basic['性别']
            if md_basic.get('手机号') and info['手机号'] == '':
                info['手机号'] = md_basic['手机号']
            if md_basic.get('联系电话') and info['联系电话'] == '':
                info['联系电话'] = md_basic['联系电话']
            if md_basic.get('住址') and info['住址'] == '':
                info['住址'] = md_basic['住址']
            if md_basic.get('地址') and info['地址'] == '':
                info['地址'] = md_basic['地址']
            if md_basic.get('职业') and info['职业'] == '':
                info['职业'] = md_basic['职业']
            if md_basic.get('与投保人关系') and info['与投保人关系'] == '':
                info['与投保人关系'] = md_basic['与投保人关系']
            
            md_addresses = md_info.get('其他地址', [])
            if md_addresses:
                info['其他地址'].extend(md_addresses)
            
            policies = md_info.get('保单列表', [])
            if policies:
                info['保单列表'] = policies
        
        unorganized = source_data.get('备份待整理档案')
        if unorganized:
            for policy in unorganized:
                if policy not in info['保单列表']:
                    info['保单列表'].append(policy)
        
        info['性别'] = self._correct_gender(name, info['性别'])
        
        if wiki_info and wiki_info.get('性别') and wiki_info['性别'] != info['性别']:
            if info['性别'] in ['女', '女性']:
                self.stats['gender_corrected'] += 1
        
        content = f"""# {name}

> 创建时间：{now}
> 数据来源：{', '.join([s.split('/')[-1] for s in sources if s]) or '未知'}

---

## 基本信息

"""
        
        field_order = [
            ('性别', '性别'),
            ('出生日期', '出生日期'),
            ('年龄', '年龄'),
            ('手机号', '手机号'),
            ('联系电话', '联系电话'),
            ('邮箱', '邮箱'),
            ('身份证号', '身份证号'),
            ('住址', '住址'),
            ('地址', '地址'),
            ('职业', '职业'),
            ('企业', '企业'),
            ('婚姻状况', '婚姻状况'),
            ('与投保人关系', '与投保人关系'),
        ]
        
        for display_name, key in field_order:
            if info[key]:
                content += f"- **{display_name}**: {info[key]}\n"
        
        if info['个人标签']:
            tags_str = ', '.join(info['个人标签'])
            content += f"- **个人标签**: {tags_str}\n"
        
        if info['家庭成员']:
            content += "\n### 家庭成员\n\n"
            content += "| 姓名 | 关系 |\n|------|------|\n"
            for m in info['家庭成员']:
                if isinstance(m, dict):
                    content += f"| {m.get('姓名', '')} | {m.get('关系', '')} |\n"
            content += "\n"
        
        if info['其他地址']:
            content += "\n### 其他地址\n\n"
            for addr in info['其他地址']:
                content += f"- {addr}\n"
        
        content += "\n---\n\n## 保单信息\n\n"
        
        if info['保单列表']:
            policy_num = 1
            seen_policies = set()
            
            for policy in info['保单列表']:
                if not policy or not policy.get('产品名称'):
                    continue
                
                policy_key = f"{policy.get('产品名称', '')}-{policy.get('投保人', '')}"
                if policy_key in seen_policies:
                    continue
                seen_policies.add(policy_key)
                
                product_name = policy.get('产品名称', '').strip()
                if product_name in ['暂无保单信息', '']:
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
            if src:
                src_name = Path(src).name
                content += f"- {src_name}: `{src}`\n"
        
        content += f"\n---\n*最后更新: {now}*\n"
        
        return content
    
    def process_all(self):
        """处理所有客户档案"""
        print("=" * 60)
        print("客户档案整合工具 v2")
        print("=" * 60)
        
        print("\n📂 加载已存在的档案...")
        self.load_existing_profiles()
        
        sources = {}
        
        print("\n📂 扫描 wiki_customers...")
        sources['wiki_customers'] = self.scan_wiki_customers()
        print(f"   找到 {len(sources['wiki_customers'])} 个客户档案")
        
        print("\n📂 扫描 整理后客户md文件...")
        sources['整理后客户md文件'] = self.scan_md_profiles()
        print(f"   找到 {len(sources['整理后客户md文件'])} 个客户档案")
        
        print("\n📂 扫描 备份客户档案...")
        sources['备份客户档案'] = self.scan_backup_profiles()
        print(f"   找到 {len(sources['备份客户档案'])} 个客户档案")
        
        print("\n📂 扫描 备份待整理档案...")
        sources['备份待整理档案'] = self.scan_unorganized_profiles()
        print(f"   找到 {len(sources['备份待整理档案'])} 个客户目录")
        
        matches = self.find_matching_profiles(sources)
        self.stats['total'] = len(matches)
        print(f"\n🔗 总计 {len(matches)} 个唯一客户")
        
        print("\n" + "=" * 60)
        print("开始整合...")
        print("=" * 60)
        
        for i, (name, source_data) in enumerate(matches, 1):
            print(f"\n[{i}/{len(matches)}] 整合客户：{name}")
            
            try:
                content = self.merge_profiles(name, source_data)
                
                safe_name = name.replace('/', '-').replace('\\', '-').replace('-', '_')
                output_file = OUTPUT_DIR / f"{safe_name}.md"
                output_file.write_text(content, encoding='utf-8')
                
                print(f"   ✅ 已保存: {output_file.name}")
                self.stats['success'] += 1
                self.stats['sources'][name] = len(source_data)
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
        print(f"\n📈 改进统计：")
        print(f"   生日信息补充：{self.stats['birthday_updated']} 条")
        print(f"   性别纠正：{self.stats['gender_corrected']} 条")
        print(f"\n📁 输出目录：{OUTPUT_DIR}")


def main():
    merger = CustomerProfileMergerV2()
    merger.process_all()


if __name__ == '__main__':
    main()
