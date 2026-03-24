"""
论文引用：基于大模型推理的根因分析实现

RCA（Root Cause Analysis）结构化推理引擎：
1. 接收统一分析上下文
2. 渲染 Prompt
3. 调用 LLM 进行推理
4. 解析 JSON 结果
5. 返回结构化 RCA 结果
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
import re

from app.core.prompts import (
    SYSTEM_PROMPT,
    build_rca_prompt,
    format_context_for_rca,
    validate_json_output
)


@dataclass
class RootCause:
    """根因假设"""
    cause: str
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "cause": self.cause,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence
        }


@dataclass
class RCAResult:
    """
    RCA 分析结果
    
    包含完整的根因分析输出：
    - 故障摘要
    - 根因假设列表（带置信度）
    - 推理链
    - 验证步骤
    - 修复建议
    - 数据缺口
    """
    incident_summary: str
    suspected_root_causes: List[RootCause] = field(default_factory=list)
    reasoning_chain: List[str] = field(default_factory=list)
    verification_steps: List[str] = field(default_factory=list)
    repair_suggestions: List[str] = field(default_factory=list)
    need_more_data: List[str] = field(default_factory=list)
    raw_response: str = ""
    parse_success: bool = True
    parse_error: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "incident_summary": self.incident_summary,
            "suspected_root_causes": [rc.to_dict() for rc in self.suspected_root_causes],
            "reasoning_chain": self.reasoning_chain,
            "verification_steps": self.verification_steps,
            "repair_suggestions": self.repair_suggestions,
            "need_more_data": self.need_more_data,
            "parse_success": self.parse_success
        }
    
    def get_top_cause(self) -> Optional[RootCause]:
        """获取置信度最高的根因"""
        if not self.suspected_root_causes:
            return None
        return max(self.suspected_root_causes, key=lambda x: x.confidence)


class RCAEngine:
    """
    基于 LLM + 结构化 Prompt 的 RCA 引擎
    
    RCA 分析主流程：
    
        ┌─────────────┐
        │ 统一分析上下文 │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Prompt 渲染  │
        │(上下文转文本) │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │  LLM 推理   │
        │ (结构化生成) │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ JSON 解析   │
        │ 结果验证    │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │  RCA 结果   │
        └─────────────┘
    """
    
    def __init__(self, llm_service=None):
        """
        初始化 RCA 引擎
        
        Args:
            llm_service: LLM 服务实例，如果为 None 则使用默认的 llm_service
        """
        self.llm_service = llm_service
    
    def _get_llm_service(self):
        """获取 LLM 服务"""
        if self.llm_service is None:
            from app.services import llm_service
            return llm_service
        return self.llm_service
    
    def analyze(
        self,
        context: 'AnalysisContext'
    ) -> RCAResult:
        """
        RCA 分析主流程
        
        Args:
            context: 统一分析上下文
        
        Returns:
            RCAResult: 结构化 RCA 结果
        """
        # 1. 构建上下文字典
        context_dict = format_context_for_rca(
            question=context.question,
            service=context.service,
            time_range=context.time_range,
            knowledge=context.retrieved_knowledge,
            metrics=context.metrics_summary if isinstance(context.metrics_summary, dict) 
                    else {"summaryText": str(context.metrics_summary)},
            logs=context.log_summary if isinstance(context.log_summary, dict)
                else {"summaryText": str(context.log_summary)},
            severity=context.severity
        )
        
        # 2. 渲染 Prompt
        prompt = build_rca_prompt(context_dict=context_dict)
        
        # 3. 调用 LLM
        llm_service = self._get_llm_service()
        try:
            raw_response = llm_service.call_llm(
                prompt,
                system_prompt=SYSTEM_PROMPT
            )
            
            # 如果返回的是字典而不是字符串
            if isinstance(raw_response, dict):
                raw_response = json.dumps(raw_response, ensure_ascii=False)
            elif not isinstance(raw_response, str):
                raw_response = str(raw_response)
                
        except Exception as e:
            return self._create_error_result(f"LLM 调用失败: {str(e)}")
        
        # 4. 解析 JSON 结果
        result = self._parse_result(raw_response)
        
        return result
    
    def analyze_simple(
        self,
        question: str,
        knowledge: List[str],
        metric_summary: str,
        log_summary: str
    ) -> RCAResult:
        """
        简化版 RCA 分析（兼容旧接口）
        
        Args:
            question: 用户问题
            knowledge: 知识库内容列表
            metric_summary: 指标摘要
            log_summary: 日志摘要
        
        Returns:
            RCAResult: 结构化 RCA 结果
        """
        # 构建上下文字典
        context_dict = {
            "question": question,
            "knowledge": knowledge,
            "metrics_summary": metric_summary,
            "log_summary": log_summary
        }
        
        # 渲染 Prompt
        prompt = build_rca_prompt(context_dict=context_dict)
        
        # 调用 LLM
        llm_service = self._get_llm_service()
        try:
            raw_response = llm_service.call_llm(
                prompt,
                system_prompt=SYSTEM_PROMPT
            )
            
            if isinstance(raw_response, dict):
                raw_response = json.dumps(raw_response, ensure_ascii=False)
            elif not isinstance(raw_response, str):
                raw_response = str(raw_response)
                
        except Exception as e:
            return self._create_error_result(f"LLM 调用失败: {str(e)}")
        
        # 解析结果
        return self._parse_result(raw_response)
    
    def _parse_result(self, raw_response: str) -> RCAResult:
        """
        解析 LLM 返回的 JSON 结果
        
        Args:
            raw_response: LLM 原始响应
        
        Returns:
            RCAResult: 解析后的结果
        """
        # 验证 JSON
        is_valid, parsed_or_error = validate_json_output(raw_response)
        
        if not is_valid:
            return self._create_error_result(parsed_or_error)
        
        try:
            data = json.loads(parsed_or_error)
            
            # 解析根因列表
            root_causes = []
            for rc_data in data.get("suspected_root_causes", []):
                root_causes.append(RootCause(
                    cause=rc_data.get("cause", ""),
                    confidence=rc_data.get("confidence", 0.0),
                    supporting_evidence=rc_data.get("supporting_evidence", []),
                    contradicting_evidence=rc_data.get("contradicting_evidence", [])
                ))
            
            # 构建结果
            result = RCAResult(
                incident_summary=data.get("incident_summary", ""),
                suspected_root_causes=root_causes,
                reasoning_chain=data.get("reasoning_chain", []),
                verification_steps=data.get("verification_steps", []),
                repair_suggestions=data.get("repair_suggestions", []),
                need_more_data=data.get("need_more_data", []),
                raw_response=raw_response,
                parse_success=True
            )
            
            return result
            
        except Exception as e:
            return self._create_error_result(f"结果解析失败: {str(e)}")
    
    def _create_error_result(self, error_message: str) -> RCAResult:
        """创建错误结果"""
        return RCAResult(
            incident_summary="分析失败",
            suspected_root_causes=[],
            reasoning_chain=[],
            verification_steps=[],
            repair_suggestions=[],
            need_more_data=[],
            raw_response="",
            parse_success=False,
            parse_error=error_message
        )
    
    def analyze_with_fallback(
        self,
        context: 'AnalysisContext'
    ) -> RCAResult:
        """
        带后备方案的 RCA 分析
        
        如果 LLM 分析失败，返回基于规则的简单分析结果
        
        Args:
            context: 统一分析上下文
        
        Returns:
            RCAResult: 结构化 RCA 结果
        """
        # 尝试 LLM 分析
        result = self.analyze(context)
        
        if result.parse_success:
            return result
        
        # 后备：基于规则的简单分析
        return self._rule_based_analysis(context)
    
    def _rule_based_analysis(self, context: 'AnalysisContext') -> RCAResult:
        """
        基于规则的简单分析（后备方案）
        
        根据异常指标和日志内容推断可能的根因
        
        Args:
            context: 统一分析上下文
        
        Returns:
            RCAResult: 基于规则的简单分析结果
        """
        # 解析异常指标
        anomalies = context.anomaly_indicators
        
        # 简单的规则映射
        root_causes = []
        
        for anomaly in anomalies:
            anomaly_lower = anomaly.lower()
            
            if "cpu" in anomaly_lower:
                root_causes.append(RootCause(
                    cause="CPU 使用率异常升高，可能存在 CPU 密集型任务或攻击行为",
                    confidence=0.75,
                    supporting_evidence=[f"指标 {anomaly} 超过阈值"],
                    contradicting_evidence=[]
                ))
            
            elif "memory" in anomaly_lower or "mem" in anomaly_lower:
                root_causes.append(RootCause(
                    cause="内存使用率异常，可能存在内存泄漏或内存配置不足",
                    confidence=0.75,
                    supporting_evidence=[f"指标 {anomaly} 超过阈值"],
                    contradicting_evidence=[]
                ))
            
            elif "connection" in anomaly_lower or "conn" in anomaly_lower:
                root_causes.append(RootCause(
                    cause="数据库/服务连接异常，可能存在连接池耗尽或网络问题",
                    confidence=0.75,
                    supporting_evidence=[f"指标 {anomaly} 超过阈值"],
                    contradicting_evidence=[]
                ))
            
            elif "latency" in anomaly_lower or "delay" in anomaly_lower:
                root_causes.append(RootCause(
                    cause="系统延迟升高，可能存在性能瓶颈或网络问题",
                    confidence=0.7,
                    supporting_evidence=[f"指标 {anomaly} 超过阈值"],
                    contradicting_evidence=[]
                ))
            
            elif "error" in anomaly_lower or "fail" in anomaly_lower:
                root_causes.append(RootCause(
                    cause="系统错误率升高，可能存在代码异常或依赖服务故障",
                    confidence=0.7,
                    supporting_evidence=[f"指标 {anomaly} 超过阈值"],
                    contradicting_evidence=[]
                ))
        
        # 生成修复建议
        suggestions = [
            "检查系统监控指标，确定异常指标的具体时间点",
            "查看该时间点前后的日志，寻找相关错误信息",
            "对比正常状态和异常状态的配置差异",
            "考虑回滚最近的变更"
        ]
        
        return RCAResult(
            incident_summary=context.question,
            suspected_root_causes=root_causes,
            reasoning_chain=["基于异常指标进行规则匹配"],
            verification_steps=["验证异常指标与故障时间点的一致性"],
            repair_suggestions=suggestions,
            need_more_data=["完整的系统日志", "变更记录", "依赖服务状态"],
            raw_response="",
            parse_success=True
        )


# 便捷函数
def analyze_incident(
    question: str,
    service: str,
    time_range: str,
    knowledge: List[Dict],
    metrics: Dict,
    logs: Dict,
    llm_service=None
) -> RCAResult:
    """
    分析事故（便捷函数）
    
    Args:
        question: 用户问题
        service: 服务名称
        time_range: 时间范围
        knowledge: 知识库检索结果
        metrics: 指标摘要
        logs: 日志摘要
        llm_service: LLM 服务实例
    
    Returns:
        RCAResult: 结构化 RCA 结果
    """
    from app.core.evidence_builder import EvidenceBuilder
    
    # 构建分析上下文
    builder = EvidenceBuilder()
    context = builder.build(
        question=question,
        service=service,
        time_range=time_range,
        knowledge=knowledge,
        metrics=metrics,
        logs=logs
    )
    
    # 执行分析
    engine = RCAEngine(llm_service=llm_service)
    return engine.analyze(context)
