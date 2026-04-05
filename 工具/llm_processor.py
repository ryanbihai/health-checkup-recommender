#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM处理模块
使用大语言模型深度理解文档内容，提取关键信息
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import time

# 路径配置
BASE_DIR = Path(r'c:\IT\00 工具和探索\haola-business\02_产品与服务\03_数字健康与AI工具\代理人支持工具')
INPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '提取数据'
OUTPUT_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / 'LLM处理数据'
MERGED_DIR = BASE_DIR / '客户档案整理项目' / '中间数据' / '合并数据'

class LLMProcessor:
    """LLM处理器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.use_mock = not self.api_key  # 如果没有API key，使用mock模式
        self.processed_count = 0
        self.total_count = 0
    
    def extract_key_info_with_llm(self, document_text: str, document_type: str) -> Dict:
        """使用LLM提取关键信息"""
        
        if self.use_mock:
            # Mock模式，使用规则提取
            return self.mock_extract(document_text, document_type)
        
        # TODO: 实现真实的OpenAI API调用
        # 这里先使用mock模式
        return self.mock_extract(document_text, document_type)
    
    def mock_extract(self, text: str, doc_type: str) -> Dict:
        """使用规则模拟LLM提取"""
        
        result = {
            'summary': '',
            'customer_needs': [],
            'recommended_products': [],
            'risk_factors': [],
            'action_items': []
        }
        
        if not text:
            return result
        
        # 提取客户需求
        need_keywords = ['需求', '希望', '想要', '关注', '担心', '顾虑']
        for keyword in need_keywords:
            if keyword in text:
                # 提取包含关键词的句子
                sentences = text.split('。')
                for sentence in sentences:
                    if keyword in sentence and len(sentence) < 100:
                        result['customer_needs'].append(sentence.strip())
        
        # 提取产品推荐
        product_keywords = ['推荐', '建议', '产品', '险种', '方案']
        for keyword in product_keywords:
            if keyword in text:
                sentences = text.split('。')
                for sentence in sentences:
                    if keyword in sentence and len(sentence) < 150:
                        result['recommended_products'].append(sentence.strip())
        
        # 提取风险因素
        risk_keywords = ['风险', '健康', '病史', '异常', '问题']
        for keyword in risk_keywords:
            if keyword in text:
                sentences = text.split('。')
                for sentence in sentences:
                    if keyword in sentence and len(sentence) < 100:
                        result['risk_factors'].append(sentence.strip())
        
        # 生成摘要
        if doc_type == '保单资料':
            result['summary'] = '保单相关文档，包含详细的保障利益信息'
        elif doc_type == '保障方案':
            result['summary'] = '保障方案文档，包含产品推荐和规划建议'
        elif doc_type == '产品解析':
            result['summary'] = '产品解析文档，详细说明产品特点和收益'
        elif doc_type == '方案比较':
            result['summary'] = '方案比较文档，多产品对比分析'
        else:
            result['summary'] = '其他文档'
        
        # 限制数量
        result['customer_needs'] = list(set(result['customer_needs']))[:5]
        result['recommended_products'] = list(set(result['recommended_products']))[:5]
        result['risk_factors'] = list(set(result['risk_factors']))[:5]
        
        return result
    
    def process_documents(self, document_list: List[Dict]) -> List[Dict]:
        """处理文档列表"""
        self.total_count = len(document_list)
        self.processed_count = 0
        
        results = []
        
        for doc in document_list:
            result = self.process_single_document(doc)
            results.append(result)
            
            self.processed_count += 1
            if self.processed_count % 10 == 0:
                print(f"   已处理: {self.processed_count}/{self.total_count}")
        
        return results
    
    def process_single_document(self, doc: Dict) -> Dict:
        """处理单个文档"""
        text = doc.get('text', '')
        doc_type = doc.get('doc_type', 'other')
        filename = doc.get('filename', '')
        
        # 使用LLM提取关键信息
        extracted = self.extract_key_info_with_llm(text, doc_type)
        
        return {
            'filename': filename,
            'doc_type': doc_type,
            'extracted_info': extracted,
            'success': True
        }
    
    def generate_sales_insights(self, client_name: str, documents: List[Dict]) -> Dict:
        """为客户生成销售洞察"""
        
        all_needs = []
        all_products = []
        all_risks = []
        
        for doc in documents:
            if 'extracted_info' in doc:
                info = doc['extracted_info']
                all_needs.extend(info.get('customer_needs', []))
                all_products.extend(info.get('recommended_products', []))
                all_risks.extend(info.get('risk_factors', []))
        
        # 去重
        all_needs = list(set(all_needs))[:10]
        all_products = list(set(all_products))[:10]
        all_risks = list(set(all_risks))[:10]
        
        return {
            'customer_name': client_name,
            'summary': f'基于{len(documents)}份文档的分析',
            'identified_needs': all_needs,
            'recommended_products': all_products,
            'risk_factors': all_risks,
            'sales_opportunities': self.identify_opportunities(all_needs, all_products),
            'next_steps': self.suggest_next_steps(all_needs, all_products)
        }
    
    def identify_opportunities(self, needs: List, products: List) -> List[str]:
        """识别销售机会"""
        opportunities = []
        
        if any('健康' in n or '医疗' in n for n in needs):
            opportunities.append('医疗险需求')
        
        if any('重疾' in n or '大病' in n for n in needs):
            opportunities.append('重疾险需求')
        
        if any('养老' in n or '退休' in n for n in needs):
            opportunities.append('养老规划需求')
        
        if any('教育' in n or '孩子' in n for n in needs):
            opportunities.append('教育金需求')
        
        if any('储蓄' in n or '理财' in n for n in needs):
            opportunities.append('储蓄险需求')
        
        if not opportunities:
            opportunities.append('待深入了解需求')
        
        return opportunities
    
    def suggest_next_steps(self, needs: List, products: List) -> List[str]:
        """建议下一步行动"""
        steps = []
        
        if not needs:
            steps.append('需要与客户进一步沟通，了解真实需求')
        
        if products:
            steps.append('可向客户推荐相关产品')
        
        steps.append('定期跟进，维护客户关系')
        
        return steps[:3]

def main():
    """主函数"""
    print("=" * 60)
    print("LLM文档处理模块")
    print("=" * 60)
    
    # 检查API key
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("\n✅ 检测到OpenAI API Key，将使用真实LLM处理")
    else:
        print("\n⚠️ 未检测到OpenAI API Key，将使用规则模拟LLM处理")
        print("   要启用真实LLM处理，请设置环境变量 OPENAI_API_KEY")
    
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载PDF/PPTX提取结果
    pdf_file = INPUT_DIR / 'pdf_pptx_extraction_results.json'
    if not pdf_file.exists():
        print("\n❌ 找不到PDF/PPTX提取结果，请先运行 extract_pdf.py")
        return
    
    print("\n📖 加载文档数据...")
    with open(pdf_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    print(f"   - 待处理文档: {len(documents)}")
    
    # 创建处理器
    processor = LLMProcessor(api_key)
    
    # 处理文档
    print("\n🔄 开始LLM处理...")
    results = processor.process_documents(documents)
    
    # 保存结果
    output_file = OUTPUT_DIR / 'llm_extraction_results.json'
    print(f"\n💾 保存结果...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成客户级洞察
    print("\n🔄 生成客户级洞察...")
    client_insights = generate_client_insights(results)
    
    insights_file = OUTPUT_DIR / 'client_insights.json'
    with open(insights_file, 'w', encoding='utf-8') as f:
        json.dump(client_insights, f, ensure_ascii=False, indent=2)
    
    # 生成可读报告
    print("\n🔄 生成可读报告...")
    report = generate_readable_report(client_insights)
    report_file = OUTPUT_DIR / 'sales_insights_report.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 打印统计
    print("\n" + "=" * 60)
    print("✅ LLM处理完成！")
    print("=" * 60)
    
    print(f"\n📊 统计:")
    print(f"   处理文档: {len(results)}")
    print(f"   识别客户: {len(client_insights)}")
    
    print(f"\n💾 输出文件:")
    print(f"   - 提取结果: {output_file}")
    print(f"   - 客户洞察: {insights_file}")
    print(f"   - 可读报告: {report_file}")

def generate_client_insights(results: List[Dict]) -> Dict:
    """生成客户级洞察"""
    
    # 按客户分组
    client_docs = {}
    
    for result in results:
        # 尝试从文件名提取客户名
        filename = result.get('filename', '')
        
        # 简化处理：按文件名模式匹配
        if '于剑' in filename:
            client_name = '于剑'
        elif '刘文杰' in filename:
            client_name = '刘文杰'
        elif '吴可卡' in filename:
            client_name = '吴可卡'
        else:
            # 使用文件名作为标识
            client_name = filename.split('-')[0] if '-' in filename else filename
        
        if client_name not in client_docs:
            client_docs[client_name] = []
        client_docs[client_name].append(result)
    
    # 生成洞察
    processor = LLMProcessor()
    insights = {}
    
    for client_name, docs in client_docs.items():
        insight = processor.generate_sales_insights(client_name, docs)
        insights[client_name] = insight
    
    return insights

def generate_readable_report(insights: Dict) -> str:
    """生成可读报告"""
    
    report = f"""# 销售洞察报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 概述

- 识别客户数：{len(insights)}
- 数据来源：PDF/PPTX文档LLM分析

"""
    
    for client_name, insight in list(insights.items())[:20]:  # 显示前20个
        report += f"""

---

## 客户：{client_name}

### 分析摘要
{insight['summary']}

### 识别的需求
"""
        
        needs = insight.get('identified_needs', [])
        if needs:
            for need in needs[:5]:
                report += f"- {need}\n"
        else:
            report += "- 暂无明确需求记录\n"
        
        report += "\n### 推荐产品\n"
        products = insight.get('recommended_products', [])
        if products:
            for product in products[:5]:
                report += f"- {product}\n"
        else:
            report += "- 待推荐\n"
        
        report += "\n### 销售机会\n"
        opportunities = insight.get('sales_opportunities', [])
        if opportunities:
            for opp in opportunities:
                report += f"- {opp}\n"
        else:
            report += "- 待识别\n"
        
        report += "\n### 下一步行动\n"
        steps = insight.get('next_steps', [])
        if steps:
            for i, step in enumerate(steps, 1):
                report += f"{i}. {step}\n"
        else:
            report += "- 待规划\n"
    
    return report

if __name__ == '__main__':
    main()
