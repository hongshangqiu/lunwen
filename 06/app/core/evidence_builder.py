"""
多源证据融合器模块
论文引用：多源数据融合架构图的核心实现

融合来自不同数据源（指标、日志、知识库）的证据，构建统一的分析上下文：
1. 接收用户问题
2. 接收指标摘要
3. 接收日志摘要
4. 接收知识库检索结果
5. 提取异常指标
6. 评估严重程度
7. 输出统一分析上下文
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """故障严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalysisContext:
    """
    统一分析上下文数据结构
    
    包含 RCA 分析所需的全部上下文信息：
    - 用户问题描述
    - 服务和时间范围
    - 知识库检索结果
    - 指标摘要
    - 日志摘要
    - 异常指标列表
    - 严重程度评估
    """
    question: str
    service: str
    time_range: str
    retrieved_knowledge: List[Dict] = field(default_factory=list)
    metrics_summary: Dict = field(default_factory=dict)
    log_summary: Dict = field(default_factory=dict)
    anomaly_indicators: List[str] = field(default_factory=list)
    severity: str = "medium"
    raw_metrics: Optional[Dict] = None
    raw_logs: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "question": self.question,
            "service": self.service,
            "time_range": self.time_range,
            "retrieved_knowledge": self.retrieved_knowledge,
            "metrics_summary": self.metrics_summary,
            "log_summary": self.log_summary,
            "anomaly_indicators": self.anomaly_indicators,
            "severity": self.severity
        }


class EvidenceBuilder:
    """
    多源证据融合器
    
    核心职责：
    1. 接收并验证来自各数据源的数据
    2. 提取异常指标
    3. 评估故障严重程度
    4. 构建统一的分析上下文
    
    数据流：
    ┌─────────┐    ┌──────────┐    ┌─────────┐
    │ 用户问题  │ + │ 指标摘要   │ + │ 日志摘要  │
    └────┬────┘    └────┬─────┘    └────┬─────┘
         │               │                │
         └───────────────┼────────────────┘
                         ▼
                ┌────────────────┐
                │  证据融合器     │
                │ EvidenceBuilder│
                └────────┬───────┘
                         ▼
                ┌────────────────┐
                │ 统一分析上下文  │
                │AnalysisContext │
                └────────────────┘
    """
    
    def __init__(self):
        """初始化证据融合器"""
        # 异常指标阈值配置
        self.thresholds = {
            "cpu": 80.0,        # CPU 使用率阈值
            "memory": 85.0,     # 内存使用率阈值
            "latency": 1000.0,  # 延迟阈值（毫秒）
            "error_rate": 5.0,   # 错误率阈值（%）
            "connections": 90.0,  # 连接数阈值（%）
        }
        
        # 严重程度关键词映射
        self.severity_keywords = {
            Severity.CRITICAL: ["critical", "crash", "down", "fatal", "panic", "halt", "宕机"],
            Severity.HIGH: ["error", "exception", "failed", "timeout", "unavailable"],
            Severity.MEDIUM: ["warning", "slow", "degraded", "延迟", "警告"],
            Severity.LOW: ["info", "notice", "debug", "信息"]
        }
    
    def build(
        self,
        question: str,
        service: str,
        time_range: str,
        knowledge: List[Dict],
        metrics: Dict,
        logs: Dict
    ) -> AnalysisContext:
        """
        融合多源数据构建统一上下文
        
        Args:
            question: 用户问题
            service: 服务名称
            time_range: 时间范围
            knowledge: 知识库检索结果
            metrics: 指标摘要
            logs: 日志摘要
        
        Returns:
            AnalysisContext: 统一分析上下文
        """
        # 1. 提取异常指标
        anomaly_indicators = self._extract_anomalies(metrics)
        
        # 2. 评估严重程度
        severity = self._assess_severity(metrics, logs, anomaly_indicators)
        
        # 3. 构建分析上下文
        context = AnalysisContext(
            question=question,
            service=service,
            time_range=time_range,
            retrieved_knowledge=knowledge,
            metrics_summary=self._summarize_metrics_for_llm(metrics),
            log_summary=self._summarize_logs_for_llm(logs),
            anomaly_indicators=anomaly_indicators,
            severity=severity.value,
            raw_metrics=metrics,
            raw_logs=logs
        )
        
        return context
    
    def _extract_anomalies(self, metrics: Dict) -> List[str]:
        """
        从指标中提取异常指标
        
        Args:
            metrics: 指标摘要字典
        
        Returns:
            List[str]: 异常指标名称列表
        """
        anomalies = []
        
        metric_results = metrics.get("metricResults", [])
        for metric in metric_results:
            metric_name = metric.get("metricName", "")
            metric_lower = metric_name.lower()
            
            # 检查是否异常
            if metric.get("isAbnormal", False):
                anomalies.append(metric_name)
                continue
            
            # 根据阈值判断
            for threshold_key, threshold_value in self.thresholds.items():
                if threshold_key in metric_lower:
                    max_value = metric.get("maxValue", 0)
                    if max_value > threshold_value:
                        anomalies.append(metric_name)
                        break
        
        return anomalies
    
    def _assess_severity(
        self,
        metrics: Dict,
        logs: Dict,
        anomalies: List[str]
    ) -> Severity:
        """
        评估故障严重程度
        
        综合考虑：
        1. 异常指标数量
        2. 日志中的错误/警告数量
        3. 日志中的严重关键词
        
        Args:
            metrics: 指标摘要
            logs: 日志摘要
            anomalies: 异常指标列表
        
        Returns:
            Severity: 严重程度枚举
        """
        severity_score = 0
        
        # 1. 基于异常指标数量评分
        anomaly_count = len(anomalies)
        if anomaly_count >= 3:
            severity_score += 3
        elif anomaly_count >= 2:
            severity_score += 2
        elif anomaly_count >= 1:
            severity_score += 1
        
        # 2. 基于日志严重性评分
        keyword_stats = logs.get("keywordStats", {})
        
        # 严重错误
        if keyword_stats.get("critical", 0) > 0:
            severity_score += 3
        elif keyword_stats.get("error", 0) > 5:
            severity_score += 2
        elif keyword_stats.get("error", 0) > 0:
            severity_score += 1
        
        # 警告
        if keyword_stats.get("warning", 0) > 10:
            severity_score += 1
        
        # 3. 检查日志中的严重关键词
        sample_logs = logs.get("sampleLogs", [])
        for log in sample_logs:
            log_lower = log.lower()
            for severity_level, keywords in self.severity_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in log_lower:
                        if severity_level == Severity.CRITICAL:
                            severity_score += 2
                        elif severity_level == Severity.HIGH:
                            severity_score += 1
        
        # 4. 基于指标峰值评分
        metric_results = metrics.get("metricResults", [])
        for metric in metric_results:
            max_value = metric.get("maxValue", 0)
            if max_value > 95:
                severity_score += 1
            elif max_value > 90:
                severity_score += 0.5
        
        # 5. 转换为严重程度枚举
        if severity_score >= 5:
            return Severity.CRITICAL
        elif severity_score >= 3:
            return Severity.HIGH
        elif severity_score >= 1:
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _summarize_metrics_for_llm(self, metrics: Dict) -> str:
        """
        将指标摘要转换为 LLM 可读的文本格式
        
        Args:
            metrics: 原始指标摘要
        
        Returns:
            str: 可读的指标摘要文本
        """
        # 如果已经有 summaryText，直接返回
        if "summaryText" in metrics:
            return metrics["summaryText"]
        
        # 否则生成摘要文本
        metric_results = metrics.get("metricResults", [])
        if not metric_results:
            return "没有获取到指标数据"
        
        lines = []
        for metric in metric_results:
            name = metric.get("metricName", "未知指标")
            avg_val = metric.get("avgValue", 0)
            max_val = metric.get("maxValue", 0)
            trend = metric.get("trend", "stable")
            is_abnormal = metric.get("isAbnormal", False)
            
            abnormal_str = "【异常】" if is_abnormal else ""
            trend_map = {"rising": "上升", "falling": "下降", "stable": "平稳"}
            trend_str = trend_map.get(trend, trend)
            
            lines.append(
                f"- {name}: 平均 {avg_val:.1f}, 最大 {max_val:.1f}, 趋势{trend_str} {abnormal_str}"
            )
        
        return "\n".join(lines)
    
    def _summarize_logs_for_llm(self, logs: Dict) -> str:
        """
        将日志摘要转换为 LLM 可读的文本格式
        
        Args:
            logs: 原始日志摘要
        
        Returns:
            str: 可读的日志摘要文本
        """
        # 如果已经有 summaryText，直接返回
        if "summaryText" in logs:
            return logs["summaryText"]
        
        # 否则生成摘要文本
        keyword_stats = logs.get("keywordStats", {})
        sample_logs = logs.get("sampleLogs", [])
        
        lines = []
        
        # 错误统计
        error_count = keyword_stats.get("error", 0)
        warning_count = keyword_stats.get("warning", 0)
        
        if error_count > 0:
            lines.append(f"日志中发现 {error_count} 条错误日志，{warning_count} 条警告日志。")
        elif warning_count > 0:
            lines.append(f"日志中发现 {warning_count} 条警告日志。")
        else:
            lines.append("日志中未发现明显异常。")
        
        # 添加样本日志
        if sample_logs:
            lines.append("\n关键日志样本：")
            for log in sample_logs[:5]:
                lines.append(f"- {log}")
        
        return "\n".join(lines)
    
    def format_context_for_prompt(self, context: AnalysisContext) -> str:
        """
        将分析上下文格式化为 Prompt 友好的文本
        
        Args:
            context: 分析上下文
        
        Returns:
            str: 格式化的上下文字符串
        """
        lines = []
        
        # 问题描述
        lines.append("## 故障分析任务")
        lines.append(f"### 用户问题")
        lines.append(f"{context.question}")
        lines.append("")
        
        # 服务和时间信息
        lines.append(f"### 服务信息")
        lines.append(f"- 服务名称: {context.service}")
        lines.append(f"- 分析时间范围: {context.time_range}")
        lines.append(f"- 严重程度: {context.severity.upper()}")
        lines.append("")
        
        # 异常指标
        if context.anomaly_indicators:
            lines.append(f"### 异常指标")
            for indicator in context.anomaly_indicators:
                lines.append(f"- {indicator}")
            lines.append("")
        
        # 指标摘要
        lines.append(f"### 指标摘要")
        lines.append(context.metrics_summary)
        lines.append("")
        
        # 日志摘要
        lines.append(f"### 日志摘要")
        lines.append(context.log_summary)
        lines.append("")
        
        # 知识库检索结果
        if context.retrieved_knowledge:
            lines.append(f"### 相关知识库内容")
            for i, kb in enumerate(context.retrieved_knowledge, 1):
                title = kb.get("metadata", {}).get("title", kb.get("source", ""))
                content = kb.get("content", "")[:300]
                score = kb.get("score", 0)
                lines.append(f"[{i}] {title} (相关度: {score:.2f})")
                lines.append(f"    {content}...")
            lines.append("")
        
        return "\n".join(lines)
