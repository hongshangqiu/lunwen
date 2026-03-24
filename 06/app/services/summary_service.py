from typing import Dict, List
from app.services import prometheus_service, log_service, knowledge_service, llm_service


def get_metrics_summary(service_name: str, start_time: str, end_time: str, metrics: List[str]) -> Dict:
    """
    获取指标摘要
    """
    return prometheus_service.summarize_metrics(service_name, start_time, end_time, metrics)


def get_logs_summary(service_name: str, start_time: str, end_time: str, keywords: List[str], limit: int = 20) -> Dict:
    """
    获取日志摘要
    """
    log_lines = log_service.read_logs(service_name, start_time, end_time, keywords, limit)
    return log_service.summarize_logs(log_lines)


def get_knowledge_chunks(query: str, service_name: str = None, top_k: int = 3) -> List[Dict]:
    """
    获取知识库检索结果
    """
    return knowledge_service.search_knowledge(query, service_name, top_k)


def run_ai_analysis(question: str, knowledge: List[str], metric_summary: str, log_summary: str) -> Dict:
    """
    运行 AI 分析
    """
    return llm_service.analyze_incident(question, knowledge, metric_summary, log_summary)
