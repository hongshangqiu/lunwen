"""
实验数据模块
论文引用：定义测试场景和评估数据

提供测试用的故障场景和评估基准数据：
- 预定义的故障场景
- 场景参数配置
- 预期结果（ground truth）
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class FaultType(Enum):
    """故障类型枚举"""
    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    DB_CONNECTION = "db_connection"
    NETWORK_LATENCY = "network_latency"
    SLOW_SQL = "slow_sql"
    SERVICE_AVALANCHE = "service_avalanche"
    DISK_FULL = "disk_full"
    UNKNOWN = "unknown"


@dataclass
class TestScene:
    """
    测试场景定义
    
    Attributes:
        scene_id: 场景唯一标识
        scene_name: 场景名称
        description: 场景描述
        fault_type: 故障类型
        service: 服务名称
        time_range: 时间范围
        metrics: 要查询的指标列表
        keywords: 日志关键词
        question: 分析问题
        expected_issue: 预期故障原因
        expected_root_cause: 预期根因
        difficulty: 难度等级 (easy/medium/hard)
    """
    scene_id: str
    scene_name: str
    description: str
    fault_type: FaultType
    service: str
    time_range: str
    metrics: List[str]
    keywords: List[str]
    question: str
    expected_issue: str
    expected_root_cause: str
    difficulty: str = "medium"


# 预定义测试场景
TEST_SCENES = [
    TestScene(
        scene_id="scene_cpu_spike",
        scene_name="CPU 使用率飙升",
        description="服务 CPU 使用率突然升高到 95% 以上",
        fault_type=FaultType.CPU_SPIKE,
        service="hotel-service",
        time_range="last_1h",
        metrics=["cpu_usage", "request_count"],
        keywords=["CPU", "spike", "intensive", "high"],
        question="为什么服务的 CPU 使用率突然飙升？",
        expected_issue="CPU 密集型计算任务",
        expected_root_cause="存在 CPU 密集型后台任务或计算逻辑异常",
        difficulty="easy"
    ),
    TestScene(
        scene_id="scene_db_conn",
        scene_name="数据库连接池耗尽",
        description="数据库连接池耗尽，服务响应缓慢",
        fault_type=FaultType.DB_CONNECTION,
        service="hotel-service",
        time_range="last_1h",
        metrics=["db_connections", "cpu_usage", "error_rate"],
        keywords=["timeout", "connection", "pool", "exhausted"],
        question="为什么服务在该时间窗内响应变慢？",
        expected_issue="数据库连接池耗尽",
        expected_root_cause="数据库连接泄露或连接池配置过小",
        difficulty="medium"
    ),
    TestScene(
        scene_id="scene_memory_leak",
        scene_name="内存泄漏",
        description="服务内存使用率持续升高，可能存在内存泄漏",
        fault_type=FaultType.MEMORY_LEAK,
        service="hotel-service",
        time_range="last_1h",
        metrics=["memory_usage", "gc_count"],
        keywords=["memory", "leak", "OOM", "heap"],
        question="服务的内存使用率持续上升，是什么原因？",
        expected_issue="内存泄漏",
        expected_root_cause="对象未正确释放导致内存泄漏",
        difficulty="medium"
    ),
    TestScene(
        scene_id="scene_network_latency",
        scene_name="网络延迟增加",
        description="服务间调用延迟显著增加",
        fault_type=FaultType.NETWORK_LATENCY,
        service="hotel-service",
        time_range="last_1h",
        metrics=["latency", "request_count"],
        keywords=["timeout", "latency", "delay", "slow"],
        question="服务间调用延迟突然增加，怎么排查？",
        expected_issue="网络延迟或服务雪崩",
        expected_root_cause="网络抖动或下游服务性能下降",
        difficulty="hard"
    ),
    TestScene(
        scene_id="scene_slow_sql",
        scene_name="慢 SQL 查询",
        description="数据库查询变慢，影响整体响应时间",
        fault_type=FaultType.SLOW_SQL,
        service="hotel-service",
        time_range="last_1h",
        metrics=["p95_latency", "db_connections"],
        keywords=["Slow query", "Scan", "WARNING"],
        question="查询接口极其缓慢，请定位原因。",
        expected_issue="缺少索引的全表扫描",
        expected_root_cause="SQL 查询缺少索引导致全表扫描",
        difficulty="medium"
    ),
    TestScene(
        scene_id="scene_service_avalanche",
        scene_name="服务雪崩",
        description="下游服务故障导致上游服务也出现错误",
        fault_type=FaultType.SERVICE_AVALANCHE,
        service="hotel-service",
        time_range="last_1h",
        metrics=["error_rate", "request_count"],
        keywords=["500", "Internal Server Error", "avalanche"],
        question="服务支付接口报错率突增，请分析原因。",
        expected_issue="后端逻辑异常导致雪崩",
        expected_root_cause="依赖服务故障导致级联失败",
        difficulty="hard"
    ),
    TestScene(
        scene_id="scene_disk_full",
        scene_name="磁盘空间不足",
        description="磁盘使用率接近 100%，影响服务运行",
        fault_type=FaultType.DISK_FULL,
        service="hotel-service",
        time_range="last_1h",
        metrics=["iowait", "disk_usage"],
        keywords=["No space", "Disk full", "CRITICAL"],
        question="系统提示磁盘空间不足，该如何处理？",
        expected_issue="日志暴增占用磁盘",
        expected_root_cause="日志文件未轮转或大量临时文件未清理",
        difficulty="easy"
    ),
]


def get_scene_by_id(scene_id: str) -> Optional[TestScene]:
    """根据 ID 获取测试场景"""
    for scene in TEST_SCENES:
        if scene.scene_id == scene_id:
            return scene
    return None


def get_scenes_by_difficulty(difficulty: str) -> List[TestScene]:
    """根据难度获取测试场景"""
    return [s for s in TEST_SCENES if s.difficulty == difficulty]


def get_scenes_by_fault_type(fault_type: FaultType) -> List[TestScene]:
    """根据故障类型获取测试场景"""
    return [s for s in TEST_SCENES if s.fault_type == fault_type]


def get_all_scenes() -> List[TestScene]:
    """获取所有测试场景"""
    return TEST_SCENES.copy()


# ==================== 评估基准 ====================

@dataclass
class EvaluationBenchmark:
    """
    评估基准数据
    
    包含每个场景的标准评估结果
    """
    scene_id: str
    ground_truth_root_cause: str
    acceptable_causes: List[str]  # 可接受的根因关键词
    required_evidence: List[str]  # 必须包含的证据
    expected_confidence_range: tuple  # 预期置信度范围
    typical_resolution_time: int  # 典型解决时间（秒）


# 预定义评估基准
EVALUATION_BENCHMARKS = {
    "scene_cpu_spike": EvaluationBenchmark(
        scene_id="scene_cpu_spike",
        ground_truth_root_cause="CPU 密集型计算任务",
        acceptable_causes=["CPU", "密集", "高负载", "计算"],
        required_evidence=["CPU 使用率", "指标异常"],
        expected_confidence_range=(0.7, 0.95),
        typical_resolution_time=60
    ),
    "scene_db_conn": EvaluationBenchmark(
        scene_id="scene_db_conn",
        ground_truth_root_cause="数据库连接池耗尽",
        acceptable_causes=["连接池", "连接", "数据库", "pool", "exhausted"],
        required_evidence=["连接", "超时", "数据库"],
        expected_confidence_range=(0.65, 0.90),
        typical_resolution_time=120
    ),
    "scene_memory_leak": EvaluationBenchmark(
        scene_id="scene_memory_leak",
        ground_truth_root_cause="内存泄漏",
        acceptable_causes=["内存", "泄漏", "leak", "memory", "OOM"],
        required_evidence=["内存使用率", "持续上升"],
        expected_confidence_range=(0.65, 0.90),
        typical_resolution_time=180
    ),
    "scene_network_latency": EvaluationBenchmark(
        scene_id="scene_network_latency",
        ground_truth_root_cause="网络延迟",
        acceptable_causes=["网络", "延迟", "latency", "timeout"],
        required_evidence=["延迟", "网络"],
        expected_confidence_range=(0.50, 0.80),
        typical_resolution_time=240
    ),
    "scene_slow_sql": EvaluationBenchmark(
        scene_id="scene_slow_sql",
        ground_truth_root_cause="SQL 缺少索引",
        acceptable_causes=["SQL", "索引", "慢查询", "全表扫描"],
        required_evidence=["SQL", "查询", "索引"],
        expected_confidence_range=(0.60, 0.85),
        typical_resolution_time=300
    ),
    "scene_service_avalanche": EvaluationBenchmark(
        scene_id="scene_service_avalanche",
        ground_truth_root_cause="级联失败",
        acceptable_causes=["雪崩", "级联", "依赖", "downstream", "avalanche"],
        required_evidence=["错误率", "依赖服务"],
        expected_confidence_range=(0.50, 0.75),
        typical_resolution_time=360
    ),
    "scene_disk_full": EvaluationBenchmark(
        scene_id="scene_disk_full",
        ground_truth_root_cause="日志/临时文件占用",
        acceptable_causes=["磁盘", "空间", "日志", "disk", "full"],
        required_evidence=["磁盘", "空间"],
        expected_confidence_range=(0.70, 0.95),
        typical_resolution_time=60
    ),
}


def get_benchmark(scene_id: str) -> Optional[EvaluationBenchmark]:
    """获取场景的评估基准"""
    return EVALUATION_BENCHMARKS.get(scene_id)
