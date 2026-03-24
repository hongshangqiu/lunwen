# 标准操作程序 (SOP): 数据库连接故障处理 (ID: SOP-DB-002)

## 1. 现象描述 (Symptoms)
- **业务表现**: 下单接口 `/order` 返回 500 错误。
- **健康检查**: `/health` 接口返回 `unhealthy`。
- **日志特征**: 出现 `Database connection pool exhausted` 或 `Unable to connect to Database Cluster`。

## 2. 诊断步骤 (Diagnostics)
1. **连接数核查**: 检查数据库服务器的最大连接数配置。
2. **连接泄露排查**: 查看是否有长时间未关闭的 SQL 事务。
3. **注入检查**: 确认日志中是否含有 `FAULT INJECTED: Database connection`。

## 3. 修复方案 (Mitigation)
- **清理连接**: 重启连接池或数据库实例。
- **故障恢复**: 若为模拟注入，调用 `/fault/db/stop`。
- **应用优化**: 增加数据库连接池配置 (`MAX_POOL_SIZE`)。

---
*版本: 1.1 | 更新时间: 2026-03-05*
