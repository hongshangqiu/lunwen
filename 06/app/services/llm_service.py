import json
import re
from typing import List, Dict
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.core.prompts import RCA_PROMPT, SYSTEM_PROMPT

# 尝试导入 OpenAI，如果失败则使用模拟实现
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# 全局 LLM 客户端单例
_llm_client = None

def get_llm_client() -> OpenAI:
    """
    获取全局 LLM 客户端（单例模式）
    """
    global _llm_client
    if _llm_client is None:
        if HAS_OPENAI and LLM_API_KEY:
            _llm_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    return _llm_client


def build_analysis_prompt(question: str, knowledge: List[str], metric_summary: str, log_summary: str) -> str:
    """
    构建分析用的 Prompt
    """
    knowledge_text = "\n".join(f"- {k[:200]}..." if len(k) > 200 else f"- {k}" for k in knowledge) if knowledge else "无"
    
    return RCA_PROMPT.format(
        question=question,
        knowledge=knowledge_text,
        metric_summary=metric_summary,
        log_summary=log_summary,
    )


def call_llm(prompt: str) -> Dict:
    """
    调用大模型进行分析
    """
    # 如果没有 API Key，使用模拟响应
    if not LLM_API_KEY:
        return get_mock_analysis_result()
    
    if not HAS_OPENAI:
        return get_mock_analysis_result()
    
    try:
        client = get_llm_client()
        if client is None:
            return get_mock_analysis_result()
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        
        # 尝试解析 JSON
        content = re.sub(r'^```json\s*', '', content.strip())
        content = re.sub(r'^```\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        
        return json.loads(content)
    
    except Exception as e:
        print(f"LLM 调用失败: {e}")
        return get_mock_analysis_result()


def get_mock_analysis_result() -> Dict:
    """
    获取模拟的分析结果（用于没有 API Key 时）
    """
    return {
        "incidentSummary": "系统在指定时间窗内出现 CPU 飙升，响应延迟增加。",
        "evidence": [
            "CPU 使用率达到 100%",
            "日志中检测到 FAULT INJECTED: CPU spike"
        ],
        "possibleCause": "模拟故障注入：CPU 密集型任务导致资源耗尽。",
        "suggestions": [
            "检查是否有异常后台进程",
            "扩容计算节点",
            "优化相关计算密集型算法"
        ],
        "remediationCode": "import requests\ntry:\n    requests.post('http://localhost:8000/fault/cpu/stop')\n    print('CPU fault stopped')\nexcept Exception as e:\n    print(f'Failed: {e}')",
        "remediationDescription": "通过调用微服务的 /fault/cpu/stop 接口停止故障注入线程。",
        "uncertainty": "无"
    }


def analyze_incident(question: str, knowledge: List[str], metric_summary: str, log_summary: str) -> Dict:
    """
    分析事故的主函数
    """
    prompt = build_analysis_prompt(question, knowledge, metric_summary, log_summary)
    return call_llm(prompt)
