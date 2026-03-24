# Redis 缓存击穿与雪崩排查 SOP

## 故障特征
- `p95_latency` 突然飙升。
- 数据库 `db_connections` 瞬时达到上限，报错 "Too many connections"。
- 缓存命中率 (Cache Hit Ratio) 断崖式下跌。

## 排查步骤
1. 检查 Redis 节点是否宕机或发生主从切换。
2. 检查是否有大批量 Key 同时过期。
3. 检查是否存在热点 Key (Hot Key) 导致单分片过载。

## 修复建议
- **短期**: 开启后端接口限流，防止数据库被压垮。
- **自动修复**: 重新加载热点数据到缓存，并设置随机过期时间。

---

# 磁盘 I/O 瓶颈与空间满排查 SOP

## 故障特征
- 系统 `iowait` 指标长期超过 20%。
- 日志出现 "No space left on device" 或 "Read-only file system"。
- 应用启动缓慢或无法写入临时文件。

## 排查步骤
1. 使用 `df -h` 查看分区空间。
2. 使用 `du -sh *` 定位大文件（通常是日志或临时 dump）。
3. 使用 `iotop` 查找占用 I/O 的进程。

## 修复建议
- **自动修复**: 运行脚本清理 `/tmp` 目录或压缩 `data/logs` 中的旧日志。
- **扩容**: 挂载新的云硬盘或增加磁盘 Quota。

---

# MySQL 慢 SQL 与死锁排查 SOP

## 故障特征
- 数据库 CPU 使用率接近 100%。
- 日志中出现 "Lock wait timeout exceeded" 或 "Deadlock found"。
- `p95_latency` 随请求量线性上升。

## 排查步骤
1. 查看 `slow_query_log` 慢日志。
2. 对嫌疑 SQL 使用 `EXPLAIN` 分析索引使用情况。
3. 检查是否存在全表扫描 (Full Table Scan)。

## 修复建议
- **自动修复**: 为缺失索引的列添加紧急索引 (需谨慎)。
- **优化**: 修改应用层代码，避免深度分页（Limit 1000000）。

---

# 微服务雪崩与熔断机制排查 SOP

## 故障特征
- 整个服务链路 (Trace) 大面积超时。
- 报错 `503 Service Unavailable` 或 `429 Too Many Requests`。
- 上游服务线程池耗尽。

## 排查步骤
1. 观察调用链拓扑图，定位故障发生的“源头”节点。
2. 检查源头节点是否因为 CPU 或内存耗尽无法响应。
3. 检查重试策略是否设置过大（导致重试风暴）。

## 修复建议
- **自愈**: 立即触发 Hystrix/Sentinel 熔断，切断对故障节点的调用。
- **降级**: 核心业务优先，非核心业务（如评论、推荐）直接返回 Mock 数据。

---

# 异常流量波动与 DDoS 限流 SOP

## 故障特征
- 入口流量 (Ingress Traffic) 异常翻倍。
- 出现大量非法请求路径或来自同一 IP 段的异常访问。
- `http_requests_total` 远超正常水位。

## 排查步骤
1. 检查 Nginx 访问日志中的 IP 频率。
2. 识别异常 User-Agent 或异常参数字段。

## 修复建议
- **自愈**: 动态更新 `iptables` 或 Nginx 配置黑名单，封禁异常 IP。
- **限流**: 对受损服务开启令牌桶限流。
