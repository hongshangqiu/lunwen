"""
论文引用：提示工程设计，是 RCA 效果的关键

提供多层次、结构化的 Prompt 模板，用于指导大模型进行故障诊断：
1. 系统级 Prompt - 定义角色和能力
2. 推理 Prompt - 包含完整推理步骤
3. 输出 Prompt - 定义结构化输出格式
4. 约束 Prompt - 定义安全和准确性约束
"""
from typing import Dict, List, Optional
import json


# ==================== 系统级提示词 ====================

SYSTEM_PROMPT = """你是一名资深 SRE（网站可靠性工程师），专精于软件故障诊断。

你的专业背景：
- 10 年以上分布式系统运维经验
- 精通 Linux 内核、性能调优、容器技术
- 熟悉常见故障模式：CPU 飙升、内存泄漏、网络延迟、数据库连接池耗尽等

你的分析遵循以下原则：
1. 证据驱动：所有结论必须基于提供的指标、日志或知识库内容
2. 结构化输出：严格按照指定格式返回结果
3. 置信度评估：每个根因假设需给出置信度评分
4. 可操作建议：修复建议必须具体可执行
5. 诚实透明：证据不足时明确说明，不编造信息"""


# ==================== RCA 分析主 Prompt ====================

def build_rca_prompt(context_json: str = None, context_dict: Dict = None) -> str:
    """
    构建 RCA 分析 Prompt
    
    Args:
        context_json: JSON 格式的上下文
        context_dict: 字典格式的上下文（会转换为 JSON）
        二选一传递
    
    Returns:
        完整的 Prompt 字符串
    """
    if context_dict:
        context_json = json.dumps(context_dict, ensure_ascii=False, indent=2)
    
    prompt = f"""## 故障分析任务

### 输入上下文
```json
{context_json}
```

### 推理步骤（请按顺序思考）

**Step 1: 现象总结**
- 简洁描述系统当前的异常表现（1-2句话）

**Step 2: 证据分析**
- 从指标中识别哪些指标出现异常？变化幅度如何？
- 从日志中提取哪些关键错误信息？
- 检索到的知识库内容提供了哪些背景信息？

**Step 3: 根因假设**
- 基于证据，列出 1-3 个可能的根因
- 每个根因必须包含：
  - 原因描述
  - 置信度（0.0-1.0）
  - 支持证据列表
  - 反对证据（如有）

**Step 4: 验证计划**
- 列出验证每个根因假设需要做的具体检查

**Step 5: 修复建议**
- 针对最可能的根因，给出可操作的修复步骤

**Step 6: 数据缺口**
- 如果当前证据不足以支撑确定结论，明确说明还需要哪些数据

### 输出格式（严格遵循 JSON）

{{
    "incident_summary": "一句话故障描述",
    "suspected_root_causes": [
        {{
            "cause": "根因描述",
            "confidence": 0.85,
            "supporting_evidence": ["证据1", "证据2"],
            "contradicting_evidence": []
        }}
    ],
    "reasoning_chain": ["推理步骤1", "推理步骤2"],
    "verification_steps": ["验证步骤1", "验证步骤2"],
    "repair_suggestions": ["建议1", "建议2"],
    "need_more_data": ["缺失数据1"]
}}

### 约束
- 严禁编造系统中未出现的事实
- 如无把握，置信度不应高于 0.9
- 输出必须是可以被 json.loads() 解析的合法 JSON"""
    
    return prompt


# ==================== 向后兼容的 Prompt ====================

RCA_PROMPT = """你是一名顶级的 SRE (Site Reliability Engineer)。当前系统出现异常，请分析指标与日志，定位根因，并给出修复建议和自动化修复脚本。

### 待分析上下文：
- 问题: {question}
- 知识检索 (RAG): {knowledge}
- 指标摘要: {metric_summary}
- 日志摘要: {log_summary}

### 受控服务可用的修复 API：
- 停止 CPU 故障: requests.post('http://localhost:8000/fault/cpu/stop')
- 恢复数据库连接: requests.post('http://localhost:8000/fault/db/stop')
- 重置网络延迟: requests.post('http://localhost:8000/fault/latency/set?seconds=0')

### 输出要求：
必须以纯 JSON 格式返回，包含以下字段：
{{
    "incidentSummary": "故障现象描述",
    "evidence": ["关键证据1", "关键证据2"],
    "possibleCause": "最可能的故障根因",
    "suggestions": ["手动排查建议1", "手动排查建议2"],
    "remediationCode": "用于自动修复故障的 Python 代码脚本（需导入 requests）",
    "remediationDescription": "修复代码的逻辑说明",
    "uncertainty": "不确定性说明"
}}

注意：
1. 只输出合法 JSON。
2. remediationCode 必须是可直接在 Python 环境中运行的。
"""


# ==================== 巡检 Prompt ====================

MONITOR_PROMPT = """你是一名 7*24 小时在线的 AI 运维巡检员。请分析以下实时监控数据：

指标简报: {metrics_summary}
日志近况: {log_summary}

请判断系统当前状态是否正常。必须返回 JSON 格式：
{{
    "is_abnormal": true/false,
    "status_description": "当前状态描述",
    "risk_level": "Low/Medium/High",
    "recommended_action": "建议的操作（如果是正常则填无）"
}}
"""


# ==================== Prompt 辅助函数 ====================

def format_knowledge_for_prompt(knowledge: List[Dict]) -> str:
    """
    将知识库检索结果格式化为 Prompt 友好的文本
    
    Args:
        knowledge: 知识库检索结果列表
    
    Returns:
        格式化的文本
    """
    if not knowledge:
        return "未检索到相关知识库内容"
    
    lines = []
    for i, kb in enumerate(knowledge, 1):
        title = kb.get("metadata", {}).get("title", kb.get("source", "未知来源"))
        content = kb.get("content", "")
        score = kb.get("score", 0)
        
        lines.append(f"[{i}] {title} (相关度: {score:.2f})")
        lines.append(f"    {content[:300]}..." if len(content) > 300 else f"    {content}")
        lines.append("")
    
    return "\n".join(lines)


def format_context_for_rca(
    question: str,
    service: str,
    time_range: str,
    knowledge: List[Dict],
    metrics: Dict,
    logs: Dict,
    severity: str = "medium"
) -> Dict:
    """
    将多源数据格式化为 RCA 上下文字典
    
    Args:
        question: 用户问题
        service: 服务名称
        time_range: 时间范围
        knowledge: 知识库检索结果
        metrics: 指标摘要
        logs: 日志摘要
        severity: 严重程度
    
    Returns:
        上下文字典
    """
    # 生成指标摘要文本
    if "summaryText" in metrics:
        metric_summary = metrics["summaryText"]
    else:
        metric_results = metrics.get("metricResults", [])
        lines = []
        for m in metric_results:
            lines.append(
                f"- {m.get('metricName')}: "
                f"均值={m.get('avgValue', 0):.1f}, "
                f"最大值={m.get('maxValue', 0):.1f}, "
                f"趋势={m.get('trend', 'unknown')}"
            )
        metric_summary = "\n".join(lines) if lines else "无指标数据"
    
    # 生成日志摘要文本
    if "summaryText" in logs:
        log_summary = logs["summaryText"]
    else:
        stats = logs.get("keywordStats", {})
        error_count = stats.get("error", 0)
        warning_count = stats.get("warning", 0)
        log_summary = f"错误日志: {error_count}条, 警告日志: {warning_count}条"
    
    # 提取异常指标
    anomaly_indicators = []
    for m in metrics.get("metricResults", []):
        if m.get("isAbnormal", False):
            anomaly_indicators.append(m.get("metricName", ""))
    
    return {
        "question": question,
        "service": {
            "name": service,
            "time_range": time_range
        },
        "severity": severity,
        "anomaly_indicators": anomaly_indicators,
        "metrics_summary": metric_summary,
        "log_summary": log_summary,
        "log_samples": logs.get("sampleLogs", [])[:5],
        "knowledge_base": [
            {
                "title": kb.get("metadata", {}).get("title", kb.get("source", "")),
                "content": kb.get("content", ""),
                "relevance_score": kb.get("score", 0)
            }
            for kb in knowledge
        ]
    }


def validate_json_output(response: str) -> tuple[bool, str]:
    """
    验证 LLM 输出是否为合法的 JSON
    
    Args:
        response: LLM 返回的原始响应
    
    Returns:
        (is_valid, parsed_json_or_error)
    """
    import re
    
    # 移除 markdown 代码块标记
    cleaned = re.sub(r'^```json\s*', '', response.strip())
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    
    try:
        parsed = json.loads(cleaned)
        return True, json.dumps(parsed, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return False, f"JSON 解析错误: {str(e)}"


# ==================== 快速分析 Prompt ====================

QUICK_RCA_PROMPT = """你是一个 SRE 故障分析助手。根据以下信息，快速给出故障可能原因和修复建议：

问题：{question}
异常指标：{anomalies}
错误日志：{errors}

请用 JSON 格式返回：
{{
    "quick_diagnosis": "一句话诊断",
    "likely_cause": "最可能的原因",
    "confidence": 0.85,
    "quick_fix": "快速修复建议"
}}
"""
