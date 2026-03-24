"""
Evaluation Experiments Package

提供四组对比实验的测试场景和评估器：
- test_scenes: 测试场景定义
- evaluator: 实验评估器
"""
from evaluation.experiments.test_scenes import (
    TestScene,
    FaultType,
    TEST_SCENES,
    get_scene_by_id,
    get_all_scenes,
    EvaluationBenchmark,
    get_benchmark
)
from evaluation.experiments.evaluator import (
    ExperimentBase,
    LLMOnlyExperiment,
    RAGOnlyExperiment,
    RAGWithRealtimeExperiment,
    FullMethodExperiment,
    ComparativeEvaluator,
    run_comparative_experiments
)

__all__ = [
    "TestScene",
    "FaultType",
    "TEST_SCENES",
    "get_scene_by_id",
    "get_all_scenes",
    "EvaluationBenchmark",
    "get_benchmark",
    "ExperimentBase",
    "LLMOnlyExperiment",
    "RAGOnlyExperiment",
    "RAGWithRealtimeExperiment",
    "FullMethodExperiment",
    "ComparativeEvaluator",
    "run_comparative_experiments"
]
