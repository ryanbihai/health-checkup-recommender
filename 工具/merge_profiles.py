#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案合并脚本
将提取的文档数据与现有客户档案合并
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Set
from collections import defaultdict

# 路径配置
BASE_DIR = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具')
INPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据'
OUTPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '合并数据'
CLIENT_BASE = BASE_DIR / '客户档案'

# 冲突检测的优先级（值越大优先级越高）
FIELD_PRIORITY = {
    '姓名': 100,
    '手机号': 90,
    '身份证号': 85,
    '出生日期': 80,
    '性别': 75,
    '邮箱': 70,
    '住址': 60,
    '职业': 50,
}

class ClientMerger:
    """客户档案合并器"""
    
    def __init__(self):
        self.excel_data = []
        self.pdf_data = []
        self.existing_profiles = {}
        self.merged_profiles = {}
        self.conflicts = []
        
    def load_data(self):
        """加载所有数据"""
        print("📖 加载数据...")
        
        # 加载Excel提取结果
        excel_file = INPUT_DIR / 'excel_extraction_results.json'
        if excel_file.exists():
            with open(excel_file, 'r', encoding='utf-8') as f:
                self.excel_data = json.load(f)
            print(f"   - Excel数据: {len(self.excel_data)} 条")
        
        # 加载PDF/PPTX提取结果
        pdf_file = INPUT_DIR / 'pdf_pptx_extraction_results.json'
        if pdf_file.exists():
            with open(pdf_file, 'r', encoding='utf-8') as f:
                self.pdf_data = json.load(f)
            print(f"   - PDF/PPTX数据: {len(self.pdf_data)} 条")
        
        # 加载现有客户档案
        self.load_existing_profiles()
    
    def load_existing_profiles(self):
        """加载现有客户档案"""
        profile_dir = CLIENT_BASE / '客户档案'
        
        if not profile_dir.exists():
            print("   ⚠️ 现有客户档案目录不存在")
            return
        
        for md_file in profile_dir.rglob('*.md'):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取客户名
                name_match = re.search(r'# 客户档案[：:]?\s*(.+)', content)
                if name_match:
                    name = name_match.group(1).strip()
                    self.existing_profiles[name] = {
                        'filepath': str(md_file),
                        'content': content,
                        'modified': md_file.stat().st_mtime
                    }
            except Exception as e:
                print(f"   ⚠️ 读取档案失败: {md_file.name} - {e}")
        
        print(f"   - 现有档案: {len(self.existing_profiles)} 条")
    
    def extract_field_from_profile(self, content: str, field: str) -> str:
        """从档案内容提取字段值"""
        patterns = [
            rf'{field}[：:]\s*([^\n]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if value and value != '待确认' and value != '待补充':
                    return value
        return ''
    
    def detect_conflicts(self, client_name: str, sources: Dict[str, Dict]) -> List[Dict]:
        """检测数据冲突"""
        conflicts = []
        
        # 关键字段冲突检测
        key_fields = ['姓名', '手机号', '身份证号', '出生日期', '性别']
        
        for field in key_fields:
            values = {}
            for source_name, source_data in sources.items():
                if field in source_data and source_data[field]:
                    value = str(source_data[field]).strip()
                    if value and value not in ['待确认', '待补充', '']:
                        values[source_name] = value
            
            if len(values) > 1:
                # 检测冲突
                unique_values = set(values.values())
                if len(unique_values) > 1:
                    conflict = {
                        'field': field,
                        'client_name': client_name,
                        'values': values,
                        'conflict_type': 'multi_value',
                        'priority': FIELD_PRIORITY.get(field, 50),
                        'sources': list(values.keys())
                    }
                    conflicts.append(conflict)
        
        return conflicts
    
    def merge_client_data(self, client_name: str, sources: Dict[str, Dict]) -> Dict:
        """合并单个客户的数据"""
        merged = {
            'client_name': client_name,
            'sources': list(sources.keys()),
            'data': {},
            'documents': []
        }
        
        # 按优先级合并字段
        for field, priority in sorted(FIELD_PRIORITY.items(), key=lambda x: x[1], reverse=True):
            value = ''
            source = ''
            
            for source_name, source_data in sources.items():
                if field in source_data:
                    field_value = str(source_data[field]).strip()
                    if field_value and field_value not in ['待确认', '待补充', '']:
                        value = field_value
                        source = source_name
                        break
            
            if value:
                merged['data'][field] = {
                    'value': value,
                    'source': source
                }
        
        # 收集文档信息
        for source_name, source_data in sources.items():
            if 'documents' in source_data:
                merged['documents'].extend(source_data['documents'])
        
        return merged
    
    def generate_markdown(self, merged_data: Dict) -> str:
        """生成Markdown格式的客户档案"""
        client_name = merged_data['client_name']
        data = merged_data['data']
        documents = merged_data['documents']
        
        # 基本信息部分
        basic_info = []
        for field in ['姓名', '性别', '出生日期', '年龄', '手机号', '邮箱', '身份证号', '住址', '职业']:
            if field in data:
                value = data[field]['value']
                source = data[field]['source']
                basic_info.append(f'{field}：{value}')
            else:
                basic_info.append(f'{field}：待确认')
        
        # 客户状态部分
        customer_status = [
            '客户状态：待确认',
            '来源渠道：待了解',
            '与我关系：待了解',
            '信任程度：⭐⭐⭐',
            f'建档日期：待确认',
            f'最后更新：{datetime.now().strftime("%Y-%m-%d")}'
        ]
        
        # 文档清单部分
        doc_list = []
        if documents:
            for doc in documents[:20]:  # 最多显示20个
                doc_path = doc.get('filepath', '')
                doc_type = doc.get('file_type', '')
                doc_list.append(f'- {doc_path} ({doc_type})')
        else:
            doc_list.append('- 暂无关联文档')
        
        # 生成Markdown
        md_content = f"""# 客户档案：{client_name}

## 基本信息
{chr(10).join(basic_info)}

## 客户状态
{chr(10).join(customer_status)}

## 家庭成员
- 无（待补充）

## 保单信息
### 主险
险种类别：待确认
保险公司：待确认
保额：待确认
生效日期：待确认
年缴保费：待确认
保单状态：待确认

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

## 待整理文档清单
### 关联文档
{chr(10).join(doc_list)}

### 数据来源
{chr(10).join([f'- {source}' for source in merged_data['sources']])}

## 数据冲突记录
暂无记录

## 特殊备注
待补充

---
档案创建：{datetime.now().strftime('%Y-%m-%d')} | 数据来源：{', '.join(merged_data['sources'])}
"""
        
        return md_content
    
    def process_all(self):
        """处理所有客户数据"""
        print("\n🔄 开始合并数据...")
        
        # 按客户分组数据
        client_data = defaultdict(lambda: {'excel': [], 'pdf': []})
        
        # 处理Excel数据
        for item in self.excel_data:
            client_name = item.get('client_name', '')
            if not client_name:
                continue
            
            # 尝试从数据中提取真实客户名
            if item.get('sheets'):
                first_sheet = item['sheets'][0]
                if 'key_info' in first_sheet and first_sheet['key_info']:
                    key_info = first_sheet['key_info']
                    if key_info.get('customer_name'):
                        client_name = key_info['customer_name']
            
            client_data[client_name]['excel'].append(item)
        
        # 处理PDF数据
        for item in self.pdf_data:
            client_name = item.get('client_name', '')
            if not client_name:
                continue
            
            # 尝试从数据中提取真实客户名
            if item.get('summary'):
                # 从摘要中提取客户名
                name_match = re.search(r'客户姓名[：:]\s*([^\n]+)', item['summary'])
                if name_match:
                    real_name = name_match.group(1).strip()
                    if real_name and len(real_name) >= 2:
                        client_name = real_name
            
            client_data[client_name]['pdf'].append(item)
        
        # 合并每个客户的数据
        total_clients = len(client_data)
        print(f"   - 待处理客户: {total_clients}")
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        merged_count = 0
        conflict_count = 0
        
        for i, (client_name, sources) in enumerate(client_data.items(), 1):
            if i % 10 == 0:
                print(f"\n[{i:3d}/{total_clients}] 处理: {client_name}")
            
            # 准备数据源
            merged_sources = {}
            
            # 添加Excel数据
            if sources['excel']:
                excel_info = self.extract_excel_info(sources['excel'])
                if excel_info:
                    merged_sources['Excel文档'] = excel_info
            
            # 添加PDF数据
            if sources['pdf']:
                pdf_info = self.extract_pdf_info(sources['pdf'])
                if pdf_info:
                    merged_sources['PDF文档'] = pdf_info
            
            if not merged_sources:
                continue
            
            # 检测冲突
            conflicts = self.detect_conflicts(client_name, merged_sources)
            if conflicts:
                self.conflicts.extend(conflicts)
                conflict_count += 1
            
            # 合并数据
            merged_data = self.merge_client_data(client_name, merged_sources)
            
            # 生成Markdown
            md_content = self.generate_markdown(merged_data)
            
            # 保存合并后的档案
            safe_name = re.sub(r'[<>:"/\\|?*]', '', client_name)
            output_file = OUTPUT_DIR / f'客户_{safe_name}.md'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            merged_count += 1
        
        return merged_count, conflict_count
    
    def extract_excel_info(self, excel_items: List[Dict]) -> Dict:
        """从Excel数据提取信息"""
        info = {}
        
        for item in excel_items:
            if not item.get('sheets'):
                continue
            
            for sheet in item['sheets']:
                if 'key_info' in sheet and sheet['key_info']:
                    key_info = sheet['key_info']
                    
                    if key_info.get('customer_name'):
                        info['姓名'] = key_info['customer_name']
                    
                    if key_info.get('policies'):
                        policies = key_info['policies'][:3]  # 最多3个
                        info['保单'] = policies
                    
                    if key_info.get('total_premium'):
                        info['总保费'] = key_info['total_premium']
        
        if info:
            info['documents'] = [{
                'filepath': item.get('filepath', ''),
                'file_type': 'excel'
            } for item in excel_items]
        
        return info
    
    def extract_pdf_info(self, pdf_items: List[Dict]) -> Dict:
        """从PDF数据提取信息"""
        info = {}
        
        for item in pdf_items:
            summary = item.get('summary', '')
            
            # 提取客户名
            name_match = re.search(r'客户姓名[：:]\s*([^\n]+)', summary)
            if name_match:
                real_name = name_match.group(1).strip()
                if real_name and len(real_name) >= 2:
                    info['姓名'] = real_name
            
            # 提取产品信息
            products_match = re.search(r'涉及产品[：:]\s*([^\n]+)', summary)
            if products_match:
                info['涉及产品'] = products_match.group(1).strip()[:100]
            
            # 提取文档类型
            doc_type_match = re.search(r'文档类型[：:]\s*([^\n]+)', summary)
            if doc_type_match:
                info['文档类型'] = doc_type_match.group(1).strip()
        
        if info:
            info['documents'] = [{
                'filepath': item.get('filepath', ''),
                'file_type': item.get('file_type', 'pdf'),
                'page_count': item.get('page_count', 0)
            } for item in pdf_items]
        
        return info
    
    def save_conflicts(self):
        """保存冲突报告"""
        if not self.conflicts:
            print("\n✅ 未检测到数据冲突")
            return
        
        # 按优先级排序
        self.conflicts.sort(key=lambda x: x['priority'], reverse=True)
        
        # 生成冲突报告
        conflict_report = {
            'report_time': datetime.now().isoformat(),
            'total_conflicts': len(self.conflicts),
            'conflict_details': self.conflicts
        }
        
        output_file = OUTPUT_DIR / '冲突报告.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conflict_report, f, ensure_ascii=False, indent=2)
        
        # 生成可读报告
        readable_report = self.generate_readable_conflict_report()
        readable_file = OUTPUT_DIR / '冲突报告-可读.md'
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(readable_report)
        
        print(f"\n⚠️ 检测到 {len(self.conflicts)} 个数据冲突")
        print(f"   - 详细报告: {output_file}")
        print(f"   - 可读报告: {readable_file}")
    
    def generate_readable_conflict_report(self) -> str:
        """生成可读的冲突报告"""
        report = f"""# 数据冲突报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 冲突统计
- 总冲突数：{len(self.conflicts)}

## 冲突详情

"""
        
        for i, conflict in enumerate(self.conflicts, 1):
            report += f"""### 冲突 {i}

- **字段**: {conflict['field']}
- **客户名**: {conflict['client_name']}
- **冲突类型**: {conflict['conflict_type']}
- **数据来源**:
"""
            for source, value in conflict['values'].items():
                report += f"  - {source}: {value}\n"
            
            report += "\n"
        
        return report

def main():
    """主函数"""
    print("=" * 60)
    print("客户档案合并工具")
    print("=" * 60)
    
    merger = ClientMerger()
    
    # 加载数据
    merger.load_data()
    
    # 处理合并
    merged_count, conflict_count = merger.process_all()
    
    # 保存冲突报告
    merger.save_conflicts()
    
    # 打印统计
    print("\n" + "=" * 60)
    print("✅ 合并完成！")
    print("=" * 60)
    
    print(f"\n📊 统计:")
    print(f"   合并客户档案: {merged_count}")
    print(f"   检测到冲突: {conflict_count}")
    print(f"\n💾 输出文件:")
    print(f"   - 合并档案: {OUTPUT_DIR}")
    print(f"   - 冲突报告: {OUTPUT_DIR / '冲突报告.json'}")
    print(f"   - 可读报告: {OUTPUT_DIR / '冲突报告-可读.md'}")

if __name__ == '__main__':
    main()
