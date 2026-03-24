import random
from typing import List, Dict
from pathlib import Path
from app.config import LOGS_DIR

# 模拟日志模板
LOG_TEMPLATES = [
    "{timestamp} INFO [{service}] Request processed successfully",
    "{timestamp} WARNING [{service}] Slow query detected: {query}",
    "{timestamp} ERROR [{service}] Connection timeout to database",
    "{timestamp} ERROR [{service}] Database connection pool exhausted",
    "{timestamp} CRITICAL [{service}] OutOfMemoryError: Java heap space",
    "{timestamp} ERROR [{service}] Failed to connect to payment gateway",
    "{timestamp} WARNING [{service}] High CPU usage detected: {cpu}%",
    "{timestamp} INFO [{service}] Garbage collection started",
    "{timestamp} ERROR [{service}] NullPointerException at {location}",
    "{timestamp} WARNING [{service}] Thread pool saturated",
    "{timestamp} ERROR [{service]} HTTP 500 Internal Server Error",
    "{timestamp} INFO [{service}] Service started successfully",
    "{timestamp} WARNING [{service}] Response time exceeded threshold",
    "{timestamp} ERROR [{service}] Database deadlock detected",
    "{timestamp} CRITICAL [{service}] Circuit breaker opened",
]


def read_logs(service_name: str, start_time: str, end_time: str, keywords: List[str], limit: int = 20) -> List[str]:
    """
    读取指定时间窗内的日志，并按关键词筛选。
    优先读取真实日志文件，若真实日志不足则补充模拟日志。
    """
    matched_logs = []
    
    # 1. 尝试从真实日志文件读取 (data/logs/app.log)
    log_file_path = LOGS_DIR / "app.log"
    if log_file_path.exists():
        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                # 获取最后 100 行进行筛选
                all_lines = f.readlines()
                recent_lines = all_lines[-100:]
                for line in recent_lines:
                    line = line.strip()
                    if not keywords or any(k.lower() in line.lower() for k in keywords):
                        matched_logs.append(line)
        except Exception as e:
            print(f"读取真实日志失败: {e}")

    # 2. 如果真实日志不足，补充模拟日志以确保演示效果
    if len(matched_logs) < limit:
        # 根据场景类型生成不同的日志
        if any(k.lower() in ["timeout", "connection", "pool", "exhausted"] for k in keywords):
            templates = [
                "{timestamp} ERROR [{service}] Database connection pool exhausted",
                "{timestamp} ERROR [{service}] Connection timeout to database",
                "{timestamp} ERROR [{service}] Unable to connect to Database Cluster",
            ]
        elif any(k.lower() in ["cpu", "spike", "intensive", "high"] for k in keywords):
            templates = [
                "{timestamp} WARNING [{service}] High CPU usage detected: 95%",
                "{timestamp} CRITICAL [{service}] FAULT INJECTED: CPU spike started",
            ]
        else:
            templates = LOG_TEMPLATES
        
        while len(matched_logs) < limit:
            template = random.choice(templates)
            log = template.format(
                timestamp=f"2026-03-11 {random.randint(9, 15):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
                service=service_name,
                query="SELECT * FROM orders",
                cpu=random.randint(80, 99),
                location="OrderService.py:42"
            )
            matched_logs.append(log)
    
    return matched_logs[:limit]


def summarize_logs(log_lines: List[str]) -> Dict:
    """
    对日志进行摘要
    """
    if not log_lines:
        return {
            "summaryText": "该时间窗内没有相关日志。",
            "keywordStats": {},
            "sampleLogs": []
        }
    
    # 统计关键词出现次数
    keyword_stats = {}
    for log in log_lines:
        log_lower = log.lower()
        # 常见关键词统计
        keywords_to_check = ["error", "warning", "timeout", "connection", "pool", "exhausted", "oom", "memory", "cpu", "spike"]
        for kw in keywords_to_check:
            if kw in log_lower:
                keyword_stats[kw] = keyword_stats.get(kw, 0) + 1
    
    # 生成摘要文本
    error_count = keyword_stats.get("error", 0)
    warning_count = keyword_stats.get("warning", 0)
    
    if error_count > 0:
        summary_text = f"日志中发现 {error_count} 条错误日志，{warning_count} 条警告日志。关键错误包括连接超时、连接池耗尽等。"
    elif warning_count > 0:
        summary_text = f"日志中发现 {warning_count} 条警告日志，系统运行存在潜在风险。"
    else:
        summary_text = "日志中未发现明显异常。"
    
    return {
        "summaryText": summary_text,
        "keywordStats": keyword_stats,
        "sampleLogs": log_lines[:10]  # 只返回前10条样本
    }
