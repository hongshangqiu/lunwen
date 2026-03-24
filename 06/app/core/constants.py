# 常量定义

# 指标名称映射 (用于展示)
METRIC_DISPLAY_NAMES = {
    "cpu_usage": "CPU 使用率",
    "memory_usage": "内存使用率",
    "p95_latency": "P95 延迟",
    "db_connections": "数据库连接数",
    "error_rate": "错误率",
    "request_count": "请求数",
    "gc_count": "GC 次数",
    "thread_count": "线程数",
}

# 异常阈值
ABNORMAL_THRESHOLDS = {
    "cpu_usage": 80.0,  # 80%
    "memory_usage": 85.0,  # 85%
    "p95_latency": 500.0,  # 500ms
    "db_connections": 80.0,  # 80% of max
    "error_rate": 5.0,  # 5%
}

# 日志级别
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 时间格式
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S+08:00"
