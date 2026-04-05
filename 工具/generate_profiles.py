#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案生成器
从待整理档案md生成符合客户数据结构样板标准的档案
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 导入模块
from llm_client import MiniMaxClient
from text_parser import TextParser
from prompts import create_extract_prompt

# 加载环境变量
load_dotenv()

# 路径配置
BASE_DIR = Path(r'c:\IT\02 代理人营销工具\agent-customer-management')
MD_DIR = BASE_DIR / '待整理档案md'
OUTPUT_DIR = BASE_DIR / '客户档案'
PROFILE_TEMPLATE = BASE_DIR / '客户数据结构样板.md'


class CustomerProfileGenerator:
    """客户档案生成器"""
    
    def __init__(self):
        self.parser = TextParser()
        self.llm_client = None
        self.use_llm = os.getenv('USE_LLM', 'true').lower() == 'true'
        
        if self.use_llm:
            try:
                self.llm_client = MiniMaxClient()
                print("✅ LLM客户端已初始化")
            except Exception as e:
                print(f"⚠️ LLM客户端初始化失败: {e}")
                print("   将使用纯规则模式")
                self.use_llm = False
    
    def scan_customers(self) -> List[Dict[str, Any]]:
        """
        扫描客户文件夹
        
        Returns:
            客户列表
        """
        customers = []
        
        for folder in MD_DIR.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                customer = {
                    'name': folder.name,
                    'folder': folder,
                    'files': [],
                }
                
                # 收集md文件
                for md_file in folder.rglob('*.md'):
                    if md_file.is_file():
                        customer['files'].append(md_file)
                
                # 按文件类型分类
                customer['file_count'] = len(customer['files'])
                customer['excel_count'] = sum(1 for f in customer['files'] if '**工作表**' in f.read_text(encoding='utf-8', errors='ignore'))
                customer['pdf_count'] = sum(1 for f in customer['files'] if '**页数**' in f.read_text(encoding='utf-8', errors='ignore'))
                customer['pptx_count'] = sum(1 for f in customer['files'] if '**幻灯片**' in f.read_text(encoding='utf-8', errors='ignore'))
                customer['docx_count'] = sum(1 for f in customer['files'] if '**源文件**' in f.read_text(encoding='utf-8', errors='ignore') and '.docx' in f.read_text(encoding='utf-8', errors='ignore'))
                customer['image_count'] = sum(1 for f in customer['files'] if '**文件类型: 图片**' in f.read_text(encoding='utf-8', errors='ignore'))
                
                customers.append(customer)
        
        # 按文件数量排序
        customers.sort(key=lambda x: -x['file_count'])
        
        return customers
    
    def read_all_content(self, customer: Dict) -> tuple[str, Dict[str, str]]:
        """
        读取客户所有md文件内容
        
        Args:
            customer: 客户信息
        
        Returns:
            (合并内容, 文件内容映射)
        """
        contents = []
        file_contents = {}
        
        for md_file in customer['files']:
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                file_contents[md_file.name] = content
                contents.append(f"\n\n{'='*60}\n")
                contents.append(f"文件：{md_file.name}\n")
                contents.append(f"{'='*60}\n")
                contents.append(content)
            except Exception as e:
                print(f"   读取文件失败 {md_file.name}: {e}")
        
        return '\n'.join(contents), file_contents
    
    def extract_info(self, customer: Dict) -> Dict[str, Any]:
        """
        提取客户信息
        
        Args:
            customer: 客户信息
        
        Returns:
            提取的信息
        """
        print(f"   读取 {customer['file_count']} 个md文件...")
        combined_content, file_contents = self.read_all_content(customer)
        
        # 规则提取
        print("   执行规则提取...")
        rule_results = []
        for filename, content in file_contents.items():
            result = self.parser.rule_extract(content, filename)
            rule_results.append(result)
        
        # 合并规则提取结果
        merged_result = self._merge_rule_results(rule_results)
        
        # 检查是否需要LLM
        should_trigger, reason = self.parser.should_trigger_llm(merged_result, combined_content)
        print(f"   LLM触发评估: {'是' if should_trigger else '否'} - {reason}")
        
        # LLM提取
        if should_trigger and self.use_llm and self.llm_client:
            print("   执行LLM深度提取...")
            llm_result = self._llm_extract(
                customer['name'],
                file_contents,
                combined_content
            )
            # 合并LLM结果
            merged_result.update(llm_result)
            merged_result['llm_used'] = True
        else:
            merged_result['llm_used'] = False
        
        merged_result['source_files'] = [f.name for f in customer['files']]
        
        return merged_result
    
    def _merge_rule_results(self, results: List[Dict]) -> Dict[str, Any]:
        """合并规则提取结果"""
        merged = {
            '姓名': [],
            '手机号': [],
            '身份证号': [],
            '险种': [],
            '保额': [],
            '保费': [],
            '公司': [],
            '家庭成员': [],
            '提取方法': '规则'
        }
        
        for result in results:
            for key in ['姓名', '手机号', '身份证号', '险种', '保额', '保费', '公司']:
                if key in result:
                    value = result[key]
                    if isinstance(value, list):
                        merged[key].extend(value)
                    else:
                        merged[key].append(value)
            
            if '家庭成员' in result:
                merged['家庭成员'].extend(result['家庭成员'])
        
        # 去重
        for key in ['姓名', '手机号', '险种', '保额', '保费', '公司']:
            merged[key] = list(set(merged[key]))
        
        # 去重家庭成员
        seen = set()
        unique_members = []
        for m in merged['家庭成员']:
            if m['姓名'] not in seen:
                seen.add(m['姓名'])
                unique_members.append(m)
        merged['家庭成员'] = unique_members
        
        return merged
    
    def _llm_extract(self, folder_name: str, file_contents: Dict, combined_content: str) -> Dict:
        """使用LLM提取信息"""
        try:
            # 确定主要文件类型
            doc_type = '混合文档'
            if file_contents:
                first_content = list(file_contents.values())[0]
                if '**工作表**' in first_content:
                    doc_type = 'Excel文档'
                elif '**页数**' in first_content:
                    doc_type = 'PDF文档'
                elif '**幻灯片**' in first_content:
                    doc_type = 'PPTX演示文稿'
                elif '**源文件**' in first_content:
                    doc_type = 'Word文档'
            
            prompt = create_extract_prompt(
                folder_name=folder_name,
                doc_type=doc_type,
                file_count=len(file_contents),
                content=combined_content[:15000]  # 限制长度
            )
            
            result = self.llm_client.extract_info(prompt)
            
            if 'error' in result:
                print(f"   LLM提取失败: {result['error']}")
                return {}
            
            result['提取方法'] = '规则+LLM'
            return result
            
        except Exception as e:
            print(f"   LLM提取异常: {e}")
            return {}
    
    def generate_profile(self, customer: Dict, extracted_info: Dict) -> str:
        """
        生成客户档案
        
        Args:
            customer: 客户信息
            extracted_info: 提取的信息
        
        Returns:
            档案内容
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        profile = f"""# 客户档案：[{customer['name']}]

> 生成时间：{now}
> 数据来源：{len(customer['files'])}个md文件
> 提取方式：{extracted_info.get('提取方法', '规则')}

---

## 基本信息

姓名：{' / '.join(extracted_info.get('姓名', [customer['name']])) or customer['name']}
性别：{' / '.join(extracted_info.get('性别', ['待确认'])) or '待确认'}
手机号：{' / '.join(extracted_info.get('手机号', ['待补充'])) or '待补充'}
身份证号：{' / '.join(extracted_info.get('身份证号', ['待补充'])) or '待补充'}

---

## 保单信息
"""
        
        # 保单列表
        policies = extracted_info.get('保单列表', [])
        if not policies:
            # 从规则提取的险种生成保单
            policies = []
            for i, (insurance, amount) in enumerate(zip(
                extracted_info.get('险种', [])[:5],
                extracted_info.get('保额', [])[:5]
            )):
                policies.append({
                    '险种': insurance,
                    '保额': amount,
                    '公司': extracted_info.get('公司', ['待确认'])[i] if i < len(extracted_info.get('公司', [])) else '待确认'
                })
        
        if policies:
            for i, policy in enumerate(policies, 1):
                profile += f"""
### 保单{i}
险种：{policy.get('险种', '待确认')}
公司：{policy.get('公司', '待确认')}
保额：{policy.get('保额', '待确认')}
保费：{policy.get('保费', '待确认')}
期限：{policy.get('期限', '待确认')}
"""
        else:
            profile += "\n（暂无保单信息）\n"
        
        # 家庭成员
        profile += """
---

## 家庭成员
"""
        family_members = extracted_info.get('家庭成员', [])
        if family_members:
            for member in family_members[:10]:  # 最多10个
                profile += f"- {member.get('姓名', '待确认')}，关系：{member.get('关系', '待确认')}"
                if '出生日期' in member:
                    profile += f"，出生：{member['出生日期']}"
                profile += "\n"
        else:
            profile += "（暂无家庭成员信息）\n"
        
        # 健康信息
        profile += """
---

## 健康信息
健康状况：待了解
既往病史：待了解
"""
        
        # 文档引用
        profile += """
---

## 文档引用
"""
        for i, filename in enumerate(extracted_info.get('source_files', []), 1):
            profile += f"| {i} | {filename} |\n"
        
        # 提取完整性评估
        total_fields = 10
        filled_fields = 0
        if extracted_info.get('姓名'):
            filled_fields += 2
        if extracted_info.get('手机号'):
            filled_fields += 1
        if extracted_info.get('险种'):
            filled_fields += 2
        if extracted_info.get('家庭成员'):
            filled_fields += 2
        if extracted_info.get('保单列表'):
            filled_fields += 3
        
        completeness = int(filled_fields / total_fields * 100)
        
        profile += f"""
---

## 提取完整性
- 基本信息完整度：{completeness}%
- 保单信息：{'已提取' if extracted_info.get('险种') else '待提取'}
- 家庭成员：{'已提取' if extracted_info.get('家庭成员') else '待提取'}
- LLM辅助：{'是' if extracted_info.get('llm_used') else '否'}

---
档案创建：{now}
"""
        
        return profile
    
    def process_all(self, max_customers: Optional[int] = None):
        """
        处理所有客户
        
        Args:
            max_customers: 最大处理数量，None表示处理全部
        """
        print("=" * 60)
        print("客户档案生成器")
        print("=" * 60)
        
        # 创建输出目录
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 扫描客户
        print("\n📁 扫描客户文件夹...")
        customers = self.scan_customers()
        print(f"✅ 找到 {len(customers)} 个客户")
        
        # 统计
        total_files = sum(c['file_count'] for c in customers)
        print(f"   总md文件数：{total_files}")
        
        # 处理
        if max_customers:
            customers = customers[:max_customers]
            print(f"   本次处理：{max_customers} 个客户")
        
        print("\n" + "=" * 60)
        print("开始处理...")
        print("=" * 60)
        
        success_count = 0
        error_count = 0
        
        for i, customer in enumerate(customers, 1):
            print(f"\n[{i}/{len(customers)}] 处理客户：{customer['name']}")
            print(f"   文件数：{customer['file_count']}")
            
            try:
                # 提取信息
                extracted_info = self.extract_info(customer)
                
                # 生成档案
                profile = self.generate_profile(customer, extracted_info)
                
                # 保存档案
                output_file = OUTPUT_DIR / f"客户档案_{customer['name']}.md"
                output_file.write_text(profile, encoding='utf-8')
                
                print(f"   ✅ 已生成：{output_file.name}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 处理失败：{e}")
                error_count += 1
        
        # 完成统计
        print("\n" + "=" * 60)
        print("处理完成！")
        print("=" * 60)
        print(f"\n📊 统计：")
        print(f"   总客户数：{len(customers)}")
        print(f"   成功：{success_count} ✅")
        print(f"   失败：{error_count} ❌")
        print(f"   成功率：{success_count/len(customers)*100:.1f}%")
        print(f"\n📁 输出目录：{OUTPUT_DIR}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='客户档案生成器')
    parser.add_argument('--max', type=int, default=None, help='最大处理客户数')
    parser.add_argument('--test', action='store_true', help='测试模式（处理3个客户）')
    
    args = parser.parse_args()
    
    generator = CustomerProfileGenerator()
    
    if args.test:
        generator.process_all(max_customers=3)
    else:
        generator.process_all(max_customers=args.max)


if __name__ == '__main__':
    main()
