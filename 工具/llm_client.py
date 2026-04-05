#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax LLM客户端 (OpenAI兼容模式 - Trae IDE使用)
接口：国内版 (api.minimax.chat)
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MiniMaxClient:
    """MiniMax API客户端 (OpenAI兼容模式)"""
    
    def __init__(self):
        self.api_key = os.getenv('MINIMAX_API_KEY')
        self.base_url = os.getenv('MINIMAX_BASE_URL', 'https://api.minimax.chat/v1')
        self.model = os.getenv('MODEL_NAME', 'MiniMax-M2.7')
        self.timeout = int(os.getenv('LLM_TIMEOUT', '120'))
        
        if not self.api_key:
            raise ValueError("API Key未设置")
        
        # 导入OpenAI SDK
        from openai import OpenAI
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout
        )
        print(f"✅ MiniMax客户端初始化成功")
        print(f"   Base URL: {self.base_url}")
        print(f"   模型: {self.model}")
    
    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """
        发送聊天请求到MiniMax API (OpenAI兼容模式)
        """
        try:
            print(f"   发送请求到 {self.model}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 解析响应
            result = response.choices[0].message.content
            
            # 提取并打印思考过程
            think_match = re.search(r'<think>(.*?)</think>', result, re.DOTALL)
            if think_match:
                think_content = think_match.group(1).strip()
                print(f"   [思考]: {think_content[:80]}...")
                # 移除 <think> 标签以便后续处理 JSON
                result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            else:
                print(f"   [思考]: 未返回思考过程")
                
            print(f"   响应长度: {len(result)} 字符")
            
            return result
            
        except Exception as e:
            error_msg = f"API错误: {str(e)}"
            print(f"   ❌ {error_msg}")
            return error_msg
    
    def extract_info(self, prompt: str) -> Dict[str, Any]:
        """提取信息并返回JSON格式"""
        response = self.chat([{"role": "user", "content": prompt}])
        
        try:
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                json_str = response.split('```')[1].split('```')[0]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            print(f"   JSON解析失败: {e}")
            return {"error": "JSON解析失败", "raw_response": response[:500]}


def create_extract_prompt(
    folder_name: str,
    doc_type: str,
    file_count: int,
    content: str
) -> str:
    """创建信息提取提示词"""
    prompt = f"""你是保险客户档案整理专家。请从以下md文本中提取客户信息。

【客户文件夹】：{folder_name}
【文件类型】：{doc_type}
【文件数量】：{file_count}

【md文本内容】：
{content[:15000]}

【任务】：
1. 提取客户基本信息（姓名、性别、年龄、手机号、身份证等）
2. 提取所有保单信息（险种、公司、保额、保费、期限等）
3. 识别家庭成员关系
4. 识别健康相关信息
5. 识别财务相关信息
6. 如有不确定信息，标注"待确认"

【输出格式】：严格JSON
{{
  "基本信息": {{
    "姓名": "...",
    "性别": "...",
    "手机号": "...",
    "身份证号": "..."
  }},
  "保单列表": [{{"险种": "...", "公司": "...", "保额": "..."}}],
  "家庭成员": [{{"姓名": "...", "关系": "...", "出生日期": "..."}}],
  "待确认项": ["..."]
}}
"""
    return prompt


def test_connection():
    """测试API连接"""
    try:
        client = MiniMaxClient()
        
        print("\n   发送测试请求...")
        response = client.chat([
            {"role": "user", "content": "你好，请简单回复'连接成功'"}
        ])
        
        print(f"\n   测试响应: {response[:100] if len(response) > 100 else response}")
        
        return True
    except Exception as e:
        print(f"❌ MiniMax客户端初始化失败: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("MiniMax M2.7 LLM客户端测试 (OpenAI兼容模式)")
    print("=" * 60)
    
    if test_connection():
        print("\n✅ MiniMax M2.7 API连接正常！")
    else:
        print("\n❌ MiniMax M2.7 API连接失败")
