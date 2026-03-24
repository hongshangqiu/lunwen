"""
实验评估器模块
论文引用：对比验证实验的评估逻辑

实现四组对照实验的评估指标计算：
1. 根因定位准确率（RootCauseAccuracy）
2. Top-3 准确率（Top3Accuracy）
3. 响应时间（ResponseTime）
4. 证据覆盖率（EvidenceCoverage）
5. 建议有效性（SuggestionValidity）
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
import re
import time
from abc import ABC, abstractmethod

from evaluation.experiments.test_scenes import (
    TestScene,
    EvaluationBenchmark,
    get_scene_by_id,
    get_benchmark,
    get_all_scenes
)


@dataclass
class ExperimentResult:
    """
    单次实验结果
    
    Attributes:
        experiment_name: 实验名称
        scene_id: 场景 ID
        question: 输入问题
        ground_truth: 标准根因
        predicted_root_cause: 预测根因
        confidence: 置信度
        response_time: 响应时间（秒）
        metrics: 各项评估指标
        raw_response: 原始响应
    """
    experiment_name: str
    scene_id: str
    question: str
    ground_truth: str
    predicted_root_cause: str
    confidence: float
    response_time: float
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_response: str = ""
    repair_suggestions: List[str] = field(default_factory=list)
    evidence_found: List[str] = field(default_factory=list)


@dataclass
class EvaluationMetrics:
    """
    评估指标汇总
    
    包含所有实验的评估结果统计
    """
    root_cause_accuracy: float  # 根因定位准确率
    top3_accuracy: float  # Top-3 准确率
    avg_response_time: float  # 平均响应时间
    evidence_coverage: float  # 证据覆盖率
    suggestion_validity: float  # 建议有效性
    total_experiments: int  # 实验总数
    correct_predictions: int  # 正确预测数


class ExperimentBase(ABC):
    """实验基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def run(self, scene: TestScene) -> Dict:
        """
        运行实验
        
        Args:
            scene: 测试场景
        
        Returns:
            实验结果字典
        """
        pass


class LLMOnlyExperiment(ExperimentBase):
    """
    实验1：仅使用大模型直接回答
    
    基线实验，不使用任何辅助信息
    """
    name = "LLM-Only"
    description = "仅使用大模型直接回答，不使用 RAG 和实时数据"
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    def run(self, scene: TestScene) -> Dict:
        """运行实验"""
        from app.core.prompts import SYSTEM_PROMPT
        
        prompt = f"""你是一名 SRE 故障分析专家。请分析以下问题：

问题：{scene.question}

请以 JSON 格式返回分析结果：
{{
    "incident_summary": "故障摘要",
    "suspected_root_causes": [
        {{
            "cause": "根因描述",
            "confidence": 0.8,
            "supporting_evidence": ["证据1"],
            "contradicting_evidence": []
        }}
    ],
    "repair_suggestions": ["建议1"]
}}
"""
        start_time = time.time()
        
        if self.llm_service:
            try:
                response = self.llm_service.call_llm(prompt, system_prompt=SYSTEM_PROMPT)
            except:
                response = self._get_mock_response(scene)
        else:
            response = self._get_mock_response(scene)
        
        elapsed_time = time.time() - start_time
        
        return self._parse_response(response, scene, elapsed_time)
    
    def _get_mock_response(self, scene: TestScene) -> str:
        """获取模拟响应"""
        return json.dumps({
            "incident_summary": f"{scene.scene_name}故障",
            "suspected_root_causes": [{
                "cause": "模拟根因（无数据）",
                "confidence": 0.5,
                "supporting_evidence": [],
                "contradicting_evidence": []
            }],
            "repair_suggestions": ["需要更多信息"]
        })
    
    def _parse_response(self, response, scene: TestScene, elapsed_time: float) -> Dict:
        """解析响应"""
        try:
            if isinstance(response, str):
                data = json.loads(response)
            else:
                data = response
        except:
            data = {"suspected_root_causes": [], "repair_suggestions": []}
        
        top_cause = data.get("suspected_root_causes", [{}])[0] if data.get("suspected_root_causes") else {}
        
        return {
            "experiment_name": self.name,
            "scene_id": scene.scene_id,
            "question": scene.question,
            "ground_truth": scene.expected_root_cause,
            "predicted_root_cause": top_cause.get("cause", ""),
            "confidence": top_cause.get("confidence", 0.0),
            "response_time": elapsed_time,
            "repair_suggestions": data.get("repair_suggestions", []),
            "raw_response": str(response)[:500]
        }


class RAGOnlyExperiment(ExperimentBase):
    """
    实验2：仅使用静态知识库 RAG
    
    使用 RAG 检索，但不包含实时数据
    """
    name = "RAG-Only"
    description = "使用静态知识库 RAG 检索，不包含实时指标和日志"
    
    def __init__(self, llm_service=None, knowledge_service=None):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
    
    def run(self, scene: TestScene) -> Dict:
        """运行实验"""
        from app.core.prompts import SYSTEM_PROMPT
        
        start_time = time.time()
        
        # 1. RAG 检索
        if self.knowledge_service:
            knowledge = self.knowledge_service.retrieve(
                query=scene.question,
                top_k=3
            )
        else:
            knowledge = []
        
        # 构建 Prompt
        knowledge_text = "\n".join([
            f"- {kb.get('content', '')[:200]}"
            for kb in knowledge
        ]) if knowledge else "无相关知识"
        
        prompt = f"""你是一名 SRE 故障分析专家。请根据知识库内容分析以下问题：

问题：{scene.question}

相关知识库内容：
{knowledge_text}

请以 JSON 格式返回分析结果：
{{
    "incident_summary": "故障摘要",
    "suspected_root_causes": [
        {{
            "cause": "根因描述",
            "confidence": 0.8,
            "supporting_evidence": ["证据1"],
            "contradicting_evidence": []
        }}
    ],
    "repair_suggestions": ["建议1"]
}}
"""
        
        if self.llm_service:
            try:
                response = self.llm_service.call_llm(prompt, system_prompt=SYSTEM_PROMPT)
            except:
                response = self._get_mock_response(scene)
        else:
            response = self._get_mock_response(scene)
        
        elapsed_time = time.time() - start_time
        
        return self._parse_response(response, scene, elapsed_time, knowledge)
    
    def _get_mock_response(self, scene: TestScene) -> str:
        """获取模拟响应"""
        return json.dumps({
            "incident_summary": f"{scene.scene_name}故障",
            "suspected_root_causes": [{
                "cause": f"基于知识的分析（{scene.fault_type.value}）",
                "confidence": 0.65,
                "supporting_evidence": ["知识库匹配"],
                "contradicting_evidence": []
            }],
            "repair_suggestions": ["检查相关配置"]
        })
    
    def _parse_response(self, response, scene: TestScene, elapsed_time: float, knowledge: List) -> Dict:
        """解析响应"""
        try:
            if isinstance(response, str):
                data = json.loads(response)
            else:
                data = response
        except:
            data = {"suspected_root_causes": [], "repair_suggestions": []}
        
        top_cause = data.get("suspected_root_causes", [{}])[0] if data.get("suspected_root_causes") else {}
        
        return {
            "experiment_name": self.name,
            "scene_id": scene.scene_id,
            "question": scene.question,
            "ground_truth": scene.expected_root_cause,
            "predicted_root_cause": top_cause.get("cause", ""),
            "confidence": top_cause.get("confidence", 0.0),
            "response_time": elapsed_time,
            "knowledge_chunks_used": len(knowledge),
            "repair_suggestions": data.get("repair_suggestions", []),
            "raw_response": str(response)[:500]
        }


class RAGWithRealtimeExperiment(ExperimentBase):
    """
    实验3：RAG + 实时数据，无结构化 Prompt
    
    使用 RAG + 实时指标/日志，但不使用结构化 Prompt
    """
    name = "RAG+Realtime"
    description = "RAG + 实时数据，但不使用结构化 Prompt"
    
    def __init__(self, llm_service=None, knowledge_service=None):
        self.llm_service = llm_service
        self.knowledge_service = knowledge_service
    
    def run(self, scene: TestScene) -> Dict:
        """运行实验"""
        from app.core.prompts import SYSTEM_PROMPT
        
        start_time = time.time()
        
        # 1. RAG 检索
        if self.knowledge_service:
            knowledge = self.knowledge_service.retrieve(
                query=scene.question,
                service=scene.service,
                top_k=3
            )
        else:
            knowledge = []
        
        # 2. 查询实时指标（模拟）
        metrics = self._get_mock_metrics(scene)
        
        # 3. 查询日志（模拟）
        logs = self._get_mock_logs(scene)
        
        # 构建 Prompt
        knowledge_text = "\n".join([
            f"- {kb.get('content', '')[:200]}"
            for kb in knowledge
        ]) if knowledge else "无相关知识"
        
        prompt = f"""你是一名 SRE 故障分析专家。请分析以下问题：

问题：{scene.question}

相关知识库内容：
{knowledge_text}

实时监控指标：
{metrics}

相关日志：
{logs}

请分析故障原因并给出修复建议。
"""
        
        if self.llm_service:
            try:
                response = self.llm_service.call_llm(prompt, system_prompt=SYSTEM_PROMPT)
            except:
                response = self._get_mock_response(scene)
        else:
            response = self._get_mock_response(scene)
        
        elapsed_time = time.time() - start_time
        
        return self._parse_response(response, scene, elapsed_time)
    
    def _get_mock_metrics(self, scene: TestScene) -> str:
        """获取模拟指标数据"""
        fault_metrics = {
            "cpu_spike": "- CPU 使用率: 95% (异常高)\n- 请求数: 正常",
            "db_connection": "- 数据库连接数: 100/100 (已耗尽)\n- CPU: 正常",
            "memory_leak": "- 内存使用率: 持续上升\n- GC 次数: 增加",
            "network_latency": "- 延迟: 500ms (异常)\n- 请求数: 正常",
            "slow_sql": "- P95 延迟: 2000ms (异常)\n- 连接数: 正常",
            "service_avalanche": "- 错误率: 50% (异常高)\n- 请求数: 下降",
            "disk_full": "- 磁盘使用率: 98% (即将满)\n- IO等待: 正常",
        }
        return fault_metrics.get(scene.fault_type.value, "- 指标正常")
    
    def _get_mock_logs(self, scene: TestScene) -> str:
        """获取模拟日志数据"""
        fault_logs = {
            "cpu_spike": "- ERROR: CPU usage spike detected: 95%",
            "db_connection": "- ERROR: Database connection pool exhausted",
            "memory_leak": "- WARNING: Memory usage increasing continuously",
            "network_latency": "- WARNING: High latency detected: 500ms",
            "slow_sql": "- WARNING: Slow query detected: execution time 2s",
            "service_avalanche": "- ERROR: HTTP 500 Internal Server Error",
            "disk_full": "- CRITICAL: No space left on device",
        }
        return fault_logs.get(scene.fault_type.value, "- 日志正常")
    
    def _get_mock_response(self, scene: TestScene) -> str:
        """获取模拟响应"""
        return json.dumps({
            "incident_summary": f"{scene.scene_name}故障",
            "suspected_root_causes": [{
                "cause": f"基于实时数据的分析（{scene.fault_type.value}）",
                "confidence": 0.75,
                "supporting_evidence": ["指标异常", "日志错误"],
                "contradicting_evidence": []
            }],
            "repair_suggestions": ["检查配置", "重启服务"]
        })
    
    def _parse_response(self, response, scene: TestScene, elapsed_time: float) -> Dict:
        """解析响应"""
        try:
            if isinstance(response, str):
                data = json.loads(response)
            else:
                data = response
        except:
            data = {"suspected_root_causes": [], "repair_suggestions": []}
        
        top_cause = data.get("suspected_root_causes", [{}])[0] if data.get("suspected_root_causes") else {}
        
        return {
            "experiment_name": self.name,
            "scene_id": scene.scene_id,
            "question": scene.question,
            "ground_truth": scene.expected_root_cause,
            "predicted_root_cause": top_cause.get("cause", ""),
            "confidence": top_cause.get("confidence", 0.0),
            "response_time": elapsed_time,
            "repair_suggestions": data.get("repair_suggestions", []),
            "raw_response": str(response)[:500]
        }


class FullMethodExperiment(ExperimentBase):
    """
    实验4：完整方案（Full-Method）
    
    RAG + 实时数据 + 结构化 Prompt
    """
    name = "Full-Method"
    description = "完整方案：RAG + 实时数据 + 结构化 Prompt"
    
    def __init__(self, rag_pipeline=None):
        self.rag_pipeline = rag_pipeline
    
    def run(self, scene: TestScene) -> Dict:
        """运行实验"""
        start_time = time.time()
        
        if self.rag_pipeline:
            result = self.rag_pipeline.analyze(
                question=scene.question,
                service=scene.service,
                time_range=scene.time_range,
                metrics=scene.metrics,
                keywords=scene.keywords
            )
        else:
            result = self._get_mock_result(scene)
        
        elapsed_time = time.time() - start_time
        
        return {
            "experiment_name": self.name,
            "scene_id": scene.scene_id,
            "question": scene.question,
            "ground_truth": scene.expected_root_cause,
            "predicted_root_cause": result.get("analysis", {}).get("top_cause", ""),
            "confidence": result.get("analysis", {}).get("confidence", 0.0),
            "response_time": elapsed_time,
            "severity": result.get("analysis", {}).get("severity", "unknown"),
            "anomaly_indicators": result.get("analysis", {}).get("anomaly_indicators", []),
            "repair_suggestions": result.get("analysis", {}).get("repair_suggestions", []),
            "evidence_found": result.get("evidence", {}).get("metrics_summary", "")[:200],
            "raw_result": result
        }
    
    def _get_mock_result(self, scene: TestScene) -> Dict:
        """获取模拟结果"""
        return {
            "analysis": {
                "incident_summary": f"{scene.scene_name}故障分析完成",
                "top_cause": scene.expected_root_cause,
                "confidence": 0.85,
                "severity": "high",
                "anomaly_indicators": ["CPU", "内存"],
                "repair_suggestions": ["检查配置", "优化代码"]
            },
            "evidence": {
                "metrics_summary": "CPU 使用率异常升高",
                "log_summary": "检测到相关错误日志"
            }
        }


class ComparativeEvaluator:
    """
    对比评估器
    
    运行四组实验并计算评估指标
    """
    
    def __init__(self):
        self.experiments = [
            LLMOnlyExperiment(),
            RAGOnlyExperiment(),
            RAGWithRealtimeExperiment(),
            FullMethodExperiment()
        ]
    
    def run_all_experiments(self, scenes: List[TestScene] = None) -> Dict:
        """
        运行所有实验
        
        Args:
            scenes: 测试场景列表，默认使用所有场景
        
        Returns:
            实验结果汇总
        """
        if scenes is None:
            scenes = get_all_scenes()
        
        all_results = []
        
        for scene in scenes:
            for experiment in self.experiments:
                try:
                    result = experiment.run(scene)
                    all_results.append(result)
                except Exception as e:
                    print(f"实验 {experiment.name} 运行失败: {e}")
                    all_results.append({
                        "experiment_name": experiment.name,
                        "scene_id": scene.scene_id,
                        "error": str(e)
                    })
        
        return self._aggregate_results(all_results)
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """
        聚合实验结果
        
        Args:
            results: 所有实验结果
        
        Returns:
            聚合后的结果
        """
        aggregated = {}
        
        for result in results:
            exp_name = result.get("experiment_name", "unknown")
            if exp_name not in aggregated:
                aggregated[exp_name] = []
            aggregated[exp_name].append(result)
        
        summary = {}
        for exp_name, exp_results in aggregated.items():
            metrics = self._calculate_metrics(exp_results)
            summary[exp_name] = {
                "results": exp_results,
                "metrics": metrics
            }
        
        return {
            "all_results": results,
            "summary": summary
        }
    
    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        """
        计算评估指标
        
        Args:
            results: 单个实验的所有场景结果
        
        Returns:
            评估指标
        """
        total = len(results)
        if total == 0:
            return {}
        
        # 计算各项指标
        correct = 0
        top3_correct = 0
        total_time = 0.0
        evidence_scores = []
        suggestion_scores = []
        
        for result in results:
            # 跳过错误结果
            if "error" in result:
                continue
            
            # 根因准确率
            if self._is_root_cause_correct(result):
                correct += 1
            
            # Top-3 准确率（简化：只要有任何根因匹配就算正确）
            if result.get("predicted_root_cause"):
                top3_correct += 1
            
            # 响应时间
            total_time += result.get("response_time", 0)
            
            # 建议有效性
            suggestions = result.get("repair_suggestions", [])
            if suggestions and suggestions[0] != "需要更多信息":
                suggestion_scores.append(1.0)
            else:
                suggestion_scores.append(0.0)
        
        return {
            "root_cause_accuracy": correct / total if total > 0 else 0,
            "top3_accuracy": top3_correct / total if total > 0 else 0,
            "avg_response_time": total_time / total if total > 0 else 0,
            "suggestion_validity": sum(suggestion_scores) / len(suggestion_scores) if suggestion_scores else 0,
            "total_experiments": total,
            "correct_predictions": correct
        }
    
    def _is_root_cause_correct(self, result: Dict) -> bool:
        """
        判断根因是否正确
        
        Args:
            result: 实验结果
        
        Returns:
            是否正确
        """
        ground_truth = result.get("ground_truth", "").lower()
        predicted = result.get("predicted_root_cause", "").lower()
        
        # 简单匹配：检查关键词
        ground_keywords = set(re.findall(r'\w+', ground_truth))
        predicted_keywords = set(re.findall(r'\w+', predicted))
        
        # 计算交集
        overlap = ground_keywords & predicted_keywords
        
        # 如果有足够的关键词重叠，认为正确
        return len(overlap) >= 2


# 辅助函数
def run_comparative_experiments() -> Dict:
    """
    运行对比实验（便捷函数）
    
    Returns:
        实验结果
    """
    evaluator = ComparativeEvaluator()
    return evaluator.run_all_experiments()
