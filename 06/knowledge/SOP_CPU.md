# 标准操作程序 (SOP): 应对 CPU 飙升故障

## 1. 现象描述
- 监控仪表盘显示 CPU 使用率超过 90%。
- 健康检查接口 `/health` 响应缓慢或超时。
- 业务日志中出现大量 `Warning` 或 `Critical` 级别警报。

## 2. 诊断步骤
1. **确认进程**: 使用 `ps aux --sort=-%cpu` 找到高 CPU 占用的 PID。
2. **分析日志**: 检查 `/data/app.log` 是否有 `FAULT INJECTED: CPU spike` 或循环计算记录。
3. **性能剖析**: 观察是否有大量并发密集计算任务。

## 3. 修复建议
- 若为模拟故障注入，请调用 API 路径 `/fault/cpu/stop`。
- 若为正常业务压力，建议扩容 (Scale-up) 或限流。
