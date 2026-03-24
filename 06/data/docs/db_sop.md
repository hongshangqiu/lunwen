# 数据库连接池故障排查 SOP

## 故障描述
当日志中出现 "connection pool exhausted" 或 "timeout" 时，通常意味着数据库连接已用尽。

## 排查步骤
1. 检查数据库最大连接数限制。
2. 检查应用层连接池配置 (如 HikariCP, Prisma pool size)。
3. 检查是否存在未关闭的 SQL 事务或慢查询。

## 修复建议
- 临时重启应用以释放僵死连接。
- 调大数据库端 `max_connections`。
- 优化 SQL，增加索引。
