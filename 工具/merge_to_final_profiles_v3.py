#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案最终整合工具 v3
专门增强对备份/待整理档案md的解析能力

改进点：
1. 增强表格数据提取能力
2. 从表格中提取投保人/被保人基本信息
3. 提取完整的保单详细信息
4. 正确处理同一文件中的多个保单
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


class CustomerProfileMergerV3:
    def __init__(self):
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'birthday_updated': 0,
            'gender_corrected': 0,
            'from_unorganized': 0,
            'sources': defaultdict(int)
        }
        self.existing_profiles = {}
        self.all_customer_names = set()
    
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
                    pass
        
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
                pass
        
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
                    pass
        
        return profiles
    
    def _parse_backup_profile(self, content: str) -> Dict:
        """解析备份客户档案格式"""
        info = {
            '出生日期': None, '年龄': None, '手机号': None, '邮箱': None,
            '身份证号': None, '住址': None, '职业': None, '企业': None,
            '性别': None, '姓名': None,
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
    
    def scan_unorganized_profiles(self) -> Dict[str, Dict]:
        """扫描备份/待整理档案md目录 - v3增强版"""
        profiles = defaultdict(lambda: {
            '基本信息': {},
            '保单列表': [],
            '家庭成员': [],
            '_source': '备份待整理档案'
        })
        
        if not UNORGANIZED_DIR.exists():
            return profiles
        
        for customer_dir in UNORGANIZED_DIR.iterdir():
            if not customer_dir.is_dir():
                continue
            
            customer_name = customer_dir.name
            self.all_customer_names.add(customer_name)
            
            for md_file in customer_dir.glob('*.md'):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    self._parse_unorganized_file(content, md_file.name, profiles[customer_name])
                except Exception as e:
                    pass
        
        return dict(profiles)
    
    def _parse_unorganized_file(self, content: str, filename: str, profile: Dict):
        """解析未整理档案文件 - v4增强表格解析"""
        lines = content.split('\n')
        
        policies = []
        current_policy = None
        current_section = None
        
        def parse_person_info(start_line, section):
            """解析投保人/被保人信息"""
            result = {}
            for j in range(start_line, min(start_line + 15, len(lines))):
                sub_line = lines[j].strip()
                if not sub_line.startswith('|'):
                    continue
                
                sub_parts = [p.strip() for p in sub_line.split('|') if p.strip()]
                for k, cell in enumerate(sub_parts):
                    prefix = section
                    if '姓名' in cell and k + 1 < len(sub_parts):
                        name = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if name and name not in ['姓名', '姓名：']:
                            result[f'{prefix}姓名'] = name
                    elif '性别' in cell and k + 1 < len(sub_parts):
                        gender = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if gender in ['男', '女']:
                            result[f'{prefix}性别'] = gender
                    elif '出生日期' in cell and k + 1 < len(sub_parts):
                        birth = sub_parts[k + 1].strip()
                        birth = re.sub(r'\s*00:00:00\s*$', '', birth).strip()
                        birth = birth.replace('：', '').replace(':', '').strip()
                        if birth and '出生日期' not in birth:
                            result[f'{prefix}出生日期'] = birth
                    elif '证件号码' in cell and k + 1 < len(sub_parts):
                        id_num = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if id_num and '证件号码' not in id_num:
                            result[f'{prefix}身份证'] = id_num
                    elif '手机' in cell and k + 1 < len(sub_parts) and '备用' not in cell:
                        phone = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if phone and '手机' not in phone:
                            result[f'{prefix}手机'] = phone
                    elif '通讯地址' in cell and k + 1 < len(sub_parts):
                        addr = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if addr and '通讯地址' not in addr:
                            result[f'{prefix}地址'] = addr
                    elif '与投保人关系' in cell and k + 1 < len(sub_parts):
                        rel = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if rel and '与投保人关系' not in rel:
                            result['与投保人关系'] = rel
                    elif '工作单位' in cell and k + 1 < len(sub_parts):
                        unit = sub_parts[k + 1].replace('：', '').replace(':', '').strip()
                        if unit and '工作单位' not in unit:
                            result['投保人单位'] = unit
                
                if '受益人' in sub_line:
                    break
            return result
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检测保单开始
            policy_match = re.search(r'([A-Z]{2}\d{12})保单详细信息', line)
            if policy_match:
                if current_policy and current_policy.get('投保人姓名'):
                    policies.append(current_policy)
                
                current_policy = {
                    '保单号': policy_match.group(1),
                    '险种列表': [],
                    '数据来源': filename
                }
                continue
            
            if current_policy is None:
                continue
            
            # 检测投保人标签行
            if '| 投保人 |' in line:
                person_info = parse_person_info(i + 1, '投保人')
                current_policy.update(person_info)
            
            # 检测被保人标签行
            elif '| 被保人 |' in line or '| 被保险人 |' in line:
                person_info = parse_person_info(i + 1, '被保人')
                current_policy.update(person_info)
            
            # 解析险种信息
            elif line.startswith('|') and ('| 主险 |' in line or '| 附加险 |' in line):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                # parts结构: [险种类型, 险种编码, 险种名称, 险种状态, 险种生效日, 保险期间, 交费期间, 保险金额, 险种保费]
                if len(parts) >= 6:
                    policy_info = {
                        '险种类型': parts[0],
                        '险种名称': parts[2] if len(parts) > 2 else '',
                        '险种状态': parts[3] if len(parts) > 3 else '',
                    }
                    if len(parts) > 4:
                        policy_info['险种生效日'] = parts[4]
                    if len(parts) > 5:
                        policy_info['保险期间'] = parts[5]
                    if len(parts) > 6:
                        policy_info['交费期间'] = parts[6]
                    if len(parts) > 7:
                        policy_info['保险金额'] = parts[7]
                    if len(parts) > 8:
                        policy_info['险种保费'] = parts[8]
                    current_policy['险种列表'].append(policy_info)
            
            # 解析受益人
            elif '| 受益人 |' in line or ('| 姓名 |' in line and '受益' in line):
                for sub_line in lines[i:min(i+5, len(lines))]:
                    if sub_line.startswith('|'):
                        parts = [p.strip() for p in sub_line.split('|') if p.strip()]
                        for part in parts:
                            if part and part not in ['证件类型', '证件号码', '与被保险人关系', '受益顺序', '受益比例', '姓名']:
                                current_policy['受益人姓名'] = part
                                break
                        if '配偶' in sub_line:
                            current_policy['受益人关系'] = '配偶'
                        elif '子女' in sub_line:
                            current_policy['受益人关系'] = '子女'
                        elif '父母' in sub_line:
                            current_policy['受益人关系'] = '父母'
                        if '受益人姓名' in current_policy and '受益人关系' in current_policy:
                            break
            
            # 检测新保单开始，保存当前保单
            elif re.search(r'[A-Z]{2}\d{12}保单', line) and current_policy:
                policies.append(current_policy)
                current_policy = None
        
        # 保存最后一个保单
        if current_policy and current_policy.get('投保人姓名'):
            policies.append(current_policy)
        
        # 合并险种到保单
        for policy in policies:
            if policy.get('险种列表'):
                main_rider = policy['险种列表'][0] if policy['险种列表'] else {}
                if main_rider.get('险种名称'):
                    policy['产品名称'] = main_rider['险种名称']
                    policy['险种状态'] = main_rider.get('险种状态', '')
                    policy['保险金额'] = main_rider.get('保险金额', '')
                    policy['险种保费'] = main_rider.get('险种保费', '')
                    policy['保险期间'] = main_rider.get('保险期间', '')
                    policy['生效日期'] = main_rider.get('险种生效日', '')
        
        if policies:
            profile['保单列表'].extend(policies)
            self.stats['from_unorganized'] += len(policies)
        
        # 提取家庭成员
        for policy in policies:
            for person_type in ['投保人', '被保人']:
                name_key = f'{person_type}姓名'
                name = policy.get(name_key)
                if name and name not in ['', '本人']:
                    existing = False
                    for member in profile['家庭成员']:
                        if member.get('姓名') == name:
                            existing = True
                            for k, v in policy.items():
                                if k.startswith(person_type) and k.endswith(('姓名', '性别', '出生日期', '手机', '身份证', '地址', '单位')) and not member.get(k.replace(f'{person_type}', '')):
                                    member[k.replace(f'{person_type}', '')] = v
                            break
                    if not existing:
                        gender = policy.get(f'{person_type}性别', '')
                        if not gender:
                            gender = '男' if name in MALE_NAMES else '女'
                        profile['家庭成员'].append({
                            '姓名': name,
                            '关系': policy.get('与投保人关系', '家庭成员'),
                            '性别': gender,
                            '出生日期': policy.get(f'{person_type}出生日期'),
                            '手机': policy.get(f'{person_type}手机'),
                            '身份证': policy.get(f'{person_type}身份证'),
                            '地址': policy.get(f'{person_type}地址'),
                            '单位': policy.get('投保人单位') if person_type == '投保人' else None
                        })
    
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
                info['保单列表'].extend(policies)
        
        unorganized = source_data.get('备份待整理档案')
        if unorganized:
            unorganized_basic = unorganized.get('基本信息', {})
            for key, value in unorganized_basic.items():
                if value and info.get(key) == '':
                    info[key] = value
            
            unorganized_members = unorganized.get('家庭成员', [])
            for member in unorganized_members:
                existing = False
                for existing_member in info['家庭成员']:
                    if existing_member.get('姓名') == member.get('姓名'):
                        for k, v in member.items():
                            if not existing_member.get(k) and v:
                                existing_member[k] = v
                        existing = True
                        break
                if not existing:
                    info['家庭成员'].append(member)
            
            unorganized_policies = unorganized.get('保单列表', [])
            if unorganized_policies:
                info['保单列表'].extend(unorganized_policies)
                sources.append('备份待整理档案')
        
        info['性别'] = self._correct_gender(name, info['性别'])
        
        content = f"""# {name}

> 创建时间：{now}
> 数据来源：{', '.join([s.split('/')[-1] if isinstance(s, str) and '/' in s else str(s) for s in sources[:3]]) or '未知'}

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
            content += "| 姓名 | 关系 | 性别 | 出生日期 | 手机 | 地址 |\n"
            content += "|------|------|------|----------|------|------|\n"
            for m in info['家庭成员']:
                if isinstance(m, dict):
                    content += f"| {m.get('姓名', '')} | {m.get('关系', '')} | {m.get('性别', '')} | {m.get('出生日期', '')} | {m.get('手机', '')} | {m.get('地址', '')} |\n"
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
                
                policy_key = f"{policy.get('产品名称', '')}-{policy.get('投保人', '')}-{policy.get('保单号', '')}"
                if policy_key in seen_policies:
                    continue
                seen_policies.add(policy_key)
                
                product_name = policy.get('产品名称', '') or policy.get('险种名称', '')
                if not product_name or product_name in ['暂无保单信息', '', '-']:
                    continue
                
                content += f"### 保单 {policy_num}\n\n"
                
                policy_fields = [
                    ('保险公司', '保险公司', '公司'),
                    ('保单号', '保单号', 'policy_no'),
                    ('投保人', '投保人', '投保人姓名'),
                    ('被保险人', '被保人', '被保险人', '被保人姓名'),
                    ('受益人', '受益人', '受益人姓名'),
                    ('产品名称', '产品名称', '险种名称'),
                    ('险种', '险种', '险种类型'),
                    ('保额', '保额', '保险金额'),
                    ('保费', '保费', '险种保费', '年缴保费'),
                    ('保险期间', '保险期间'),
                    ('缴费年限', '缴费年限', '交费期间'),
                    ('生效日期', '生效日期', '险种生效日'),
                    ('保单状态', '保单状态'),
                ]
                
                for field_def in policy_fields:
                    for key in field_def[1:]:
                        if key in policy and policy[key]:
                            value = str(policy[key]).strip()
                            if value and value not in ['-', '', '无', '暂无']:
                                content += f"- **{field_def[0]}**: {value}\n"
                                break
                
                if '数据来源' in policy:
                    content += f"- *来源*: {policy['数据来源']}\n"
                
                content += "\n"
                policy_num += 1
        else:
            content += "*暂无保单信息*\n\n"
        
        content += "---\n\n## 数据来源\n\n"
        for src in sources:
            if src:
                src_name = Path(src).name if isinstance(src, str) and '/' in src else str(src)
                content += f"- {src_name}\n"
        
        content += f"\n---\n*最后更新: {now}*\n"
        
        return content
    
    def process_all(self):
        """处理所有客户档案"""
        print("=" * 60)
        print("客户档案整合工具 v3")
        print("增强版：专门优化备份/待整理档案md的解析")
        print("=" * 60)
        
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
        
        print("\n📂 扫描 备份待整理档案 (v3增强解析)...")
        sources['备份待整理档案'] = self.scan_unorganized_profiles()
        print(f"   找到 {len(sources['备份待整理档案'])} 个客户目录")
        
        matches = self.find_matching_profiles(sources)
        self.stats['total'] = len(matches)
        print(f"\n🔗 总计 {len(matches)} 个唯一客户")
        
        print("\n" + "=" * 60)
        print("开始整合...")
        print("=" * 60)
        
        for i, (name, source_data) in enumerate(matches, 1):
            if i <= 5 or i % 50 == 0:
                print(f"\n[{i}/{len(matches)}] 整合客户：{name}")
            
            try:
                content = self.merge_profiles(name, source_data)
                
                safe_name = name.replace('/', '-').replace('\\', '-').replace('-', '_')
                output_file = OUTPUT_DIR / f"{safe_name}.md"
                output_file.write_text(content, encoding='utf-8')
                
                self.stats['success'] += 1
            except Exception as e:
                print(f"   ❌ 失败 {name}: {e}")
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
        print(f"\n📈 数据改进：")
        print(f"   生日信息补充：{self.stats['birthday_updated']} 条")
        print(f"   从待整理档案补充：{self.stats['from_unorganized']} 条")
        print(f"\n📁 输出目录：{OUTPUT_DIR}")


def main():
    merger = CustomerProfileMergerV3()
    merger.process_all()


if __name__ == '__main__':
    main()
