"""
RAG 编排管道模块
论文引用：原型系统的核心处理流程

端到端 RAG 编排管道，协调各服务完成故障分析任务：
1. 接收用户问题
2. RAG 检索知识库
3. 查询实时指标
4. 查询相关日志
5. 证据融合
6. RCA 推理
7. 返回结构化结果
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import time

from app.services.knowledge_service import KnowledgeService
from app.services.prometheus_service import summarize_metrics
from app.services.log_service import read_logs, summarize_logs
from app.core.evidence_builder import EvidenceBuilder, AnalysisContext
from app.services.rca_engine import RCAEngine, RCAResult


@dataclass
class PipelineConfig:
    """管道配置"""
    include_knowledge: bool = True      # 是否检索知识库
    include_metrics: bool = True        # 是否查询指标
    include_logs: bool = True          # 是否查询日志
    knowledge_top_k: int = 3           # 知识检索数量
    log_limit: int = 50                # 日志条数限制
    use_llm: bool = True               # 是否使用 LLM（False 则使用规则）


class RAGPipeline:
    """
    RAG 编排管道
    
    端到端分析流程：
    
    1. 【问题理解】解析问题意图，提取服务名、时间范围
    2. 【RAG 检索】从向量库检索相关知识
    3. 【指标查询】获取实时监控指标
    4. 【日志查询】获取相关日志
    5. 【证据融合】构建统一分析上下文
    6. 【RCA 推理】调用 LLM 进行根因分析
    7. 【结果输出】返回结构化分析结果
    """
    
    def __init__(self, config: PipelineConfig = None):
        """
        初始化 RAG 管道
        
        Args:
            config: 管道配置
        """
        self.config = config or PipelineConfig()
        self.knowledge_service = KnowledgeService()
        self.evidence_builder = EvidenceBuilder()
        self.rca_engine = RCAEngine()
    
    def analyze(
        self,
        question: str,
        service: str = None,
        time_range: str = "last_1h",
        metrics: List[str] = None,
        keywords: List[str] = None,
        config: PipelineConfig = None
    ) -> Dict:
        """
        执行端到端故障分析
        
        Args:
            question: 用户问题（自然语言）
            service: 服务名称
            time_range: 时间范围（如 "last_1h", "2024-01-01 10:00-11:00"）
            metrics: 要查询的指标列表（默认 ["cpu_usage", "memory_usage", "request_latency"]）
            keywords: 日志关键词列表
            config: 运行时配置（覆盖初始化配置）
        
        Returns:
            Dict: 包含分析结果的字典
        """
        start_time = time.time()
        
        # 合并配置
        cfg = config or self.config
        
        # 默认指标
        if metrics is None:
            metrics = ["cpu_usage", "memory_usage", "db_connections", "request_latency"]
        
        # 默认关键词
        if keywords is None:
            keywords = ["error", "warning", "exception", "timeout"]
        
        # 1. 知识检索
        knowledge_results = []
        if cfg.include_knowledge:
            knowledge_results = self._retrieve_knowledge(question, service, cfg.knowledge_top_k)
        
        # 2. 指标查询
        metrics_data = {}
        if cfg.include_metrics:
            metrics_data = self._query_metrics(service or "default", time_range, metrics)
        
        # 3. 日志查询
        logs_data = {}
        if cfg.include_logs:
            logs_data = self._query_logs(service or "default", time_range, keywords, cfg.log_limit)
        
        # 4. 证据融合
        context = self._build_context(
            question=question,
            service=service or "unknown",
            time_range=time_range,
            knowledge=knowledge_results,
            metrics=metrics_data,
            logs=logs_data
        )
        
        # 5. RCA 推理
        rca_result = self._run_rca(context, cfg.use_llm)
        
        # 6. 构建响应
        elapsed_time = time.time() - start_time
        
        return self._build_response(
            context=context,
            rca_result=rca_result,
            knowledge=knowledge_results,
            metrics=metrics_data,
            logs=logs_data,
            elapsed_time=elapsed_time
        )
    
    def _retrieve_knowledge(
        self,
        question: str,
        service: str = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        RAG 检索
        
        Args:
            question: 查询问题
            service: 服务名（用于过滤）
            top_k: 返回数量
        
        Returns:
            检索结果列表
        """
        try:
            results = self.knowledge_service.retrieve(
                query=question,
                service=service,
                top_k=top_k
            )
            return results
        except Exception as e:
            print(f"知识检索失败: {e}")
            return []
    
    def _query_metrics(
        self,
        service: str,
        time_range: str,
        metrics: List[str]
    ) -> Dict:
        """
        查询指标数据
        
        Args:
            service: 服务名
            time_range: 时间范围
            metrics: 指标列表
        
        Returns:
            指标摘要字典
        """
        try:
            # 简单处理时间范围
            start_time = "1h ago"
            end_time = "now"
            
            result = summarize_metrics(service, start_time, end_time, metrics)
            return result
        except Exception as e:
            print(f"指标查询失败: {e}")
            return {"summaryText": "指标查询失败", "metricResults": []}
    
    def _query_logs(
        self,
        service: str,
        time_range: str,
        keywords: List[str],
        limit: int = 50
    ) -> Dict:
        """
        查询日志数据
        
        Args:
            service: 服务名
            time_range: 时间范围
            keywords: 关键词列表
            limit: 返回条数
        
        Returns:
            日志摘要字典
        """
        try:
            # 简单处理时间范围
            start_time = "1h ago"
            end_time = "now"
            
            log_lines = read_logs(service, start_time, end_time, keywords, limit)
            summary = summarize_logs(log_lines)
            return summary
        except Exception as e:
            print(f"日志查询失败: {e}")
            return {"summaryText": "日志查询失败", "sampleLogs": []}
    
    def _build_context(
        self,
        question: str,
        service: str,
        time_range: str,
        knowledge: List[Dict],
        metrics: Dict,
        logs: Dict
    ) -> AnalysisContext:
        """
        构建统一分析上下文
        
        Args:
            question: 用户问题
            service: 服务名
            time_range: 时间范围
            knowledge: 知识检索结果
            metrics: 指标数据
            logs: 日志数据
        
        Returns:
            AnalysisContext: 统一分析上下文
        """
        return self.evidence_builder.build(
            question=question,
            service=service,
            time_range=time_range,
            knowledge=knowledge,
            metrics=metrics,
            logs=logs
        )
    
    def _run_rca(self, context: AnalysisContext, use_llm: bool = True) -> RCAResult:
        """
        运行 RCA 推理
        
        Args:
            context: 分析上下文
            use_llm: 是否使用 LLM
        
        Returns:
            RCAResult: RCA 结果
        """
        if use_llm:
            return self.rca_engine.analyze_with_fallback(context)
        else:
            return self.rca_engine._rule_based_analysis(context)
    
    def _build_response(
        self,
        context: AnalysisContext,
        rca_result: RCAResult,
        knowledge: List[Dict],
        metrics: Dict,
        logs: Dict,
        elapsed_time: float
    ) -> Dict:
        """
        构建最终响应
        
        Args:
            context: 分析上下文
            rca_result: RCA 结果
            knowledge: 知识检索结果
            metrics: 指标数据
            logs: 日志数据
            elapsed_time: 耗时
        
        Returns:
            响应字典
        """
        # 获取最高置信度根因
        top_cause = rca_result.get_top_cause()
        
        return {
            "success": True,
            "elapsed_time": round(elapsed_time, 2),
            "analysis": {
                "incident_summary": rca_result.incident_summary,
                "severity": context.severity,
                "anomaly_indicators": context.anomaly_indicators,
                "suspected_root_causes": rca_result.to_dict().get("suspected_root_causes", []),
                "reasoning_chain": rca_result.reasoning_chain,
                "verification_steps": rca_result.verification_steps,
                "repair_suggestions": rca_result.repair_suggestions,
                "need_more_data": rca_result.need_more_data,
                "confidence": top_cause.confidence if top_cause else 0.0,
                "top_cause": top_cause.cause if top_cause else "未知"
            },
            "evidence": {
                "metrics_summary": context.metrics_summary,
                "log_summary": context.log_summary,
                "knowledge_chunks": [
                    {
                        "content": kb.get("content", "")[:200],
                        "source": kb.get("source", ""),
                        "score": kb.get("score", 0)
                    }
                    for kb in knowledge[:3]
                ]
            },
            "raw_result": rca_result.to_dict()
        }
    
    async def analyze_async(
        self,
        question: str,
        service: str = None,
        time_range: str = "last_1h",
        metrics: List[str] = None,
        keywords: List[str] = None
    ) -> Dict:
        """
        异步版本的分析方法
        
        目前实现为同步调用，后续可优化为真正的异步
        """
        return self.analyze(
            question=question,
            service=service,
            time_range=time_range,
            metrics=metrics,
            keywords=keywords
        )


# ==================== 实验管道 ====================

class ExperimentPipeline(RAGPipeline):
    """
    实验用 RAG 管道
    
    支持不同的实验配置：
    - 仅 LLM
    - 仅 RAG
    - RAG + 实时数据
    - 完整方案（Full-Method）
    """
    
    def run_experiment(
        self,
        experiment_type: str,
        question: str,
        service: str = None,
        time_range: str = "last_1h"
    ) -> Dict:
        """
        运行指定类型的实验
        
        Args:
            experiment_type: 实验类型
                - "llm_only": 仅使用 LLM
                - "rag_only": 仅使用 RAG
                - "rag_realtime": RAG + 实时数据
                - "full_method": 完整方案
            question: 问题
            service: 服务名
            time_range: 时间范围
        
        Returns:
            实验结果
        """
        # 根据实验类型配置管道
        config = PipelineConfig()
        
        if experiment_type == "llm_only":
            config.include_knowledge = False
            config.include_metrics = False
            config.include_logs = False
            config.use_llm = True
        
        elif experiment_type == "rag_only":
            config.include_knowledge = True
            config.include_metrics = False
            config.include_logs = False
            config.use_llm = False  # 不使用结构化 Prompt
        
        elif experiment_type == "rag_realtime":
            config.include_knowledge = True
            config.include_metrics = True
            config.include_logs = True
            config.use_llm = False  # 不使用结构化 Prompt
        
        elif experiment_type == "full_method":
            config.include_knowledge = True
            config.include_metrics = True
            config.include_logs = True
            config.use_llm = True
        
        else:
            raise ValueError(f"未知的实验类型: {experiment_type}")
        
        # 运行分析
        start_time = time.time()
        result = self.analyze(
            question=question,
            service=service,
            time_range=time_range,
            config=config
        )
        elapsed_time = time.time() - start_time
        
        # 添加实验元数据
        result["experiment"] = {
            "type": experiment_type,
            "timestamp": time.time(),
            "elapsed_time": elapsed_time
        }
        
        return result


# 便捷函数
def run_full_analysis(
    question: str,
    service: str = None,
    time_range: str = "last_1h"
) -> Dict:
    """
    运行完整分析（便捷函数）
    """
    pipeline = RAGPipeline()
    return pipeline.analyze(
        question=question,
        service=service,
        time_range=time_range
    )
