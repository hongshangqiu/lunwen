import random
import requests
from typing import List, Dict
from app.config import PROMETHEUS_URL

# Demo Service 的 URL
DEMO_SERVICE_URL = "http://localhost:8000"


def query_prometheus(service_name: str, metric_name: str, start_time: str, end_time: str) -> List[float]:
    """
    从 Demo Service 获取实时指标数据。
    如果无法连接，则使用模拟数据作为后备。
    """
    # 尝试从 demo_service 获取真实数据
    try:
        response = requests.get(f"{DEMO_SERVICE_URL}/metrics/realtime", timeout=2)
        if response.status_code == 200:
            data = response.json()
            
            if "cpu" in metric_name:
                values = [m["value"] for m in data.get("cpu", [])]
                if values:
                    return values
            elif "memory" in metric_name:
                values = [m["value"] for m in data.get("memory", [])]
                if values:
                    return values
    except Exception:
        pass  # 使用后备模拟数据
    
    # 后备：模拟生成数据点
    if "cpu" in metric_name or "latency" in metric_name or "connections" in metric_name:
        return [random.uniform(70, 95) for _ in range(10)]
    return [random.uniform(20, 40) for _ in range(10)]

def summarize_single_metric(values: List[float], metric_name: str) -> Dict:
    """
    按照《一.docx》第十二点建议：指标摘要逻辑。
    计算趋势和判定异常。
    """
    if not values:
        return {
            "metricName": metric_name,
            "maxValue": 0,
            "avgValue": 0,
            "trend": "unknown",
            "isAbnormal": False,
        }

    start = values[0]
    end = values[-1]
    max_value = max(values)
    avg_value = sum(values) / len(values)

    # 趋势判定：变化超过 30% 视为有趋势
    trend = "stable"
    if end > start * 1.3:
        trend = "rising"
    elif end < start * 0.7:
        trend = "falling"

    # 异常判定：CPU/内存超过 80% 视为异常，或延迟超过阈值
    is_abnormal = False
    if "cpu" in metric_name and max_value > 80:
        is_abnormal = True
    elif "connections" in metric_name and max_value > 90:
        is_abnormal = True
    elif "latency" in metric_name and max_value > 1.0: # 假设阈值 1s
        is_abnormal = True

    return {
        "metricName": metric_name,
        "maxValue": round(max_value, 2),
        "avgValue": round(avg_value, 2),
        "trend": trend,
        "isAbnormal": is_abnormal,
    }

def summarize_metrics(service_name: str, start_time: str, end_time: str, metrics: List[str]) -> Dict:
    """
    汇总所有指标分析结果。
    """
    results = []
    abnormal_metrics = []
    
    for m in metrics:
        values = query_prometheus(service_name, m, start_time, end_time)
        res = summarize_single_metric(values, m)
        results.append(res)
        if res["isAbnormal"]:
            abnormal_metrics.append(m)

    # 生成摘要文本（用于 LLM 输入）
    if abnormal_metrics:
        summary_text = f"在监测时间窗内，{', '.join(abnormal_metrics)} 出现明显异常。其中，大部分指标呈 {results[0]['trend']} 趋势。"
    else:
        summary_text = "所有核心指标运行平稳，未见明显异常趋势。"

    return {
        "summaryText": summary_text,
        "metricResults": results
    }
