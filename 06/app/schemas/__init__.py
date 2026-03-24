from pydantic import BaseModel
from typing import List, Optional


class SceneItem(BaseModel):
    """场景列表项"""
    sceneId: str
    sceneName: str
    serviceName: str


class SceneDetail(BaseModel):
    """场景详情"""
    sceneId: str
    sceneName: str
    serviceName: str
    startTime: str
    endTime: str
    metricList: List[str]
    logKeywords: List[str]
    questionTemplate: str
    expectedIssue: Optional[str] = None


class MetricsSummaryRequest(BaseModel):
    """指标摘要请求"""
    serviceName: str
    startTime: str
    endTime: str
    metrics: List[str]


class MetricResult(BaseModel):
    """单个指标结果"""
    metricName: str
    maxValue: float
    avgValue: float
    minValue: float
    trend: str  # rising, falling, stable
    isAbnormal: bool


class MetricsSummaryResponseData(BaseModel):
    """指标摘要响应数据"""
    summaryText: str
    metricResults: List[MetricResult]


class LogsSummaryRequest(BaseModel):
    """日志摘要请求"""
    serviceName: str
    startTime: str
    endTime: str
    keywords: List[str]
    limit: int = 20


class LogsSummaryResponseData(BaseModel):
    """日志摘要响应数据"""
    summaryText: str
    keywordStats: dict
    sampleLogs: List[str]


class KnowledgeSearchRequest(BaseModel):
    """知识检索请求"""
    query: str
    serviceName: Optional[str] = None
    topK: int = 3


class KnowledgeChunk(BaseModel):
    """知识库片段"""
    content: str
    source: str
    score: float


class KnowledgeSearchResponseData(BaseModel):
    """知识检索响应数据"""
    chunks: List[KnowledgeChunk]


class AnalyzeRequest(BaseModel):
    """AI 分析请求"""
    question: str
    knowledge: List[str]
    metricSummary: str
    logSummary: str


class AnalyzeResponseData(BaseModel):
    """AI 分析响应数据"""
    incidentSummary: str
    evidence: List[str]
    possibleCause: str
    suggestions: List[str]
    uncertainty: str


class DemoRunRequest(BaseModel):
    """Demo 运行请求"""
    sceneId: str


class DemoRunResponseData(BaseModel):
    """Demo 运行响应数据"""
    scene: dict
    metrics: dict
    logs: dict
    analysis: dict
