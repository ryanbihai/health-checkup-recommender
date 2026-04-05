#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户档案提取提示词模板
基于客户数据结构样板.md设计
"""

# 系统角色设定
SYSTEM_PROMPT = """你是一位专业的保险客户档案整理专家，擅长从各种保险文档（Excel保单利益表、PDF保障方案、PPTX产品解析、DOCX情况说明）中准确提取客户信息。"""

# 信息提取提示词模板
EXTRACT_PROMPT_TEMPLATE = """{system_prompt}

请从以下md文本中提取客户信息，并严格按照JSON格式输出。

【客户文件夹】：{folder_name}
【文件类型】：{doc_type}
【文件数量】：{file_count}

【md文本内容】：
{content}

【输出要求】：
1. 严格按照下面定义的JSON字段结构输出
2. 所有字段必须填写，如无信息则填写null或空列表[]
3. 日期格式统一为YYYY-MM-DD
4. 金额单位统一为"元"，保额单位统一为"元"或"万元"
5. 关系字段参考：本人/配偶/丈夫/妻子/儿子/女儿/父亲/母亲/其他
6. 如文档中未提供某项信息，字段值设为null，不要编造信息

【JSON输出格式】：
{{
  "基本信息": {{
    "姓名": null,
    "性别": null,
    "出生日期": null,
    "年龄": null,
    "手机号": null,
    "微信号": null,
    "邮箱": null,
    "身份证号": null,
    "身份证有效期": null,
    "住址": null,
    "职业": null,
    "工作单位": null,
    "年收入": null,
    "婚姻状态": null,
    "与投保人关系": null
  }},
  "家庭成员": [
    {{
      "姓名": null,
      "关系": null,
      "出生日期": null,
      "职业": null,
      "健康状况": null,
      "备注": null
    }}
  ],
  "保单列表": [
    {{
      "险种名称": null,
      "保单号": null,
      "险种类别": null,
      "保险类型": null,
      "保险公司": null,
      "产品名称": null,
      "保单状态": null,
      "生效日期": null,
      "投保人": null,
      "被保险人": null,
      "受益人": null,
      "保额": null,
      "年缴保费": null,
      "累计保费": null,
      "缴费方式": null,
      "缴费期限": null,
      "已缴年限": null,
      "保障期限": null,
      "等待期": null,
      "犹豫期": null,
      "宽限期": null,
      "保障说明": null,
      "生存金": null,
      "满期金": null,
      "身故保险金": null,
      "现金价值": null,
      "核保结论": null,
      "特别约定": null,
      "既往症约定": null
    }}
  ],
  "健康信息": {{
    "体检日期": null,
    "体检机构": null,
    "体检结论": null,
    "体检异常指标": [],
    "既往病史": null,
    "家族病史": null,
    "健康关注": null,
    "吸烟习惯": null,
    "饮酒习惯": null,
    "运动习惯": null,
    "健康告知结果": null,
    "异常项详情": null,
    "核保日期": null,
    "核保结论": null
  }},
  "财务信息": {{
    "年收入": null,
    "主要收入来源": null,
    "可支配保费预算": null,
    "财务目标": null,
    "风险偏好": null,
    "已有养老储备": null,
    "财务备注": null
  }},
  "重要日期": {{
    "生日": null,
    "保单周年": null,
    "续费日期": null,
    "缴费提醒": null,
    "保单贷款到期日": null,
    "其他重要日期": []
  }},
  "待确认项": [],
  "数据来源": []
}}

【任务】：
1. 提取客户基本信息（姓名、性别、年龄、手机号、身份证等）
2. 提取所有保单信息（险种、公司、保额、保费、期限等）
3. 识别家庭成员关系（配偶、子女、父母等）
4. 识别健康相关信息（体检、既往病史等）
5. 识别财务相关信息（年收入、预算等）
6. 识别重要日期（生日、保单周年等）
7. 如有不确定信息，在"待确认项"中列出
8. 在"数据来源"中列出每条信息对应的源文件

请直接输出JSON，不要有其他内容："""


def create_extract_prompt(
    folder_name: str,
    doc_type: str,
    file_count: int,
    content: str
) -> str:
    """创建信息提取提示词"""
    return EXTRACT_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        folder_name=folder_name,
        doc_type=doc_type,
        file_count=file_count,
        content=content[:15000]
    )


def create_simple_prompt(content: str, field: str = None) -> str:
    """创建简单提取提示词（用于特定字段提取）"""
    if field:
        return f"""从以下文本中提取{field}信息，只返回JSON：
{content[:5000]}
"""
    return f"""从以下文本中提取关键信息，只返回JSON：
{content[:5000]}
"""
