# 内存泄漏 (Memory Leak) 排查 SOP

## 故障特征
- `memory_usage` 持续呈 `rising` 趋势，不随请求量下降而下降。
- 日志中出现 `java.lang.OutOfMemoryError` 或 Python 的 `MemoryError`。

## 排查步骤
1. 使用 `jmap` (Java) 或 `objgraph` (Python) 分析堆内存。
2. 检查缓存（Cache）是否设置了过期时间。
3. 检查单例对象中是否持有大量全局变量。

## 修复建议
- **短期**: 扩容 Pod 或重启服务。
- **长期**: 优化内存管理逻辑，关闭未使用的连接池。

---

# 网络延迟抖动 (Latency Spike) 排查 SOP

## 故障特征
- `p95_latency` 剧烈波动，但 `cpu_usage` 正常。
- 日志中出现大量的 `timeout` 或 `upstream timed out`。

## 排查步骤
1. 检查宿主机网络丢包率。
2. 检查下游依赖服务的响应时间。
3. 检查连接池是否达到最大限制。

## 修复建议
- 增加服务重试（Retry）机制。
- 调大数据库或下游服务的连接池上限。
- 开启熔断器（Circuit Breaker）。
