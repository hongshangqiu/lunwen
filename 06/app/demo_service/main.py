from fastapi import FastAPI, HTTPException, Request
import time
import logging
import os
import sys
import psutil
import threading
import random
from datetime import datetime

# 添加项目根目录到 sys.path，确保可以导入 app 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 使用统一的日志配置
from app.logging_config import setup_logger

logger = setup_logger("HotelService", "hotel_service.log")

app = FastAPI(title="Hotel Reservation Microservice")

# 存储实时指标数据（供监控面板使用）
METRICS_DATA = {
    "cpu": [],
    "memory": [],
    "requests": [],
    "errors": [],
    "latency": []
}

# 故障模拟标志位
FAULT_STATE = {
    "cpu": False,
    "memory": [],
    "latency": 0,
    "db_error": False,
    "disk_full": False,
    "slow_sql": False,
    "high_error": False
}

# --- 新增故障模拟逻辑 ---

@app.post("/fault/disk/start")
async def start_disk_fault():
    FAULT_STATE["disk_full"] = True
    logger.critical("FAULT INJECTED: Disk space full (Simulated). No space left on device: /data/logs")
    return {"message": "Disk fault injected"}

@app.post("/fault/disk/stop")
async def stop_disk_fault():
    FAULT_STATE["disk_full"] = False
    logger.info("FAULT REMOVED: Disk space cleared")
    return {"message": "Disk fault stopped"}

@app.post("/fault/slow_sql/start")
async def start_slow_sql():
    FAULT_STATE["slow_sql"] = True
    logger.warning("FAULT INJECTED: Slow SQL queries detected on table 'orders'")
    return {"message": "Slow SQL fault injected"}

@app.post("/fault/slow_sql/stop")
async def stop_slow_sql():
    FAULT_STATE["slow_sql"] = False
    logger.info("FAULT REMOVED: SQL performance normalized")
    return {"message": "Slow SQL fault stopped"}

@app.post("/fault/error_rate/start")
async def start_error_fault():
    FAULT_STATE["high_error"] = True
    logger.critical("FAULT INJECTED: Service avalanche started. High error rate on /payment")
    return {"message": "High error rate fault injected"}

@app.post("/fault/error_rate/stop")
async def stop_error_fault():
    FAULT_STATE["high_error"] = False
    logger.info("FAULT REMOVED: Service error rate recovered")
    return {"message": "High error rate fault stopped"}

@app.get("/query")
async def query_data():
    """模拟查询接口，受慢 SQL 故障影响"""
    if FAULT_STATE["slow_sql"]:
        time.sleep(random.uniform(2.0, 5.0))
        logger.warning("Slow query executed: SELECT * FROM orders WHERE status='pending' (Scan 1M rows)")
    return {"data": "some results"}

@app.post("/payment")
async def process_payment():
    """模拟支付接口，受高错误率故障影响"""
    if FAULT_STATE["high_error"]:
        logger.error("Payment failed: Internal Server Error (500)")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return {"status": "success"}

def cpu_intensive_task():
    """持续消耗 CPU 的线程"""
    while FAULT_STATE["cpu"]:
        _ = 2**20 * 2**20

@app.get("/")
async def root():
    logger.info("Accessing root endpoint")
    return {"message": "Hotel Microservice is running"}

@app.get("/health")
async def health():
    """模拟健康检查，当系统处于高压力时可能返回异常"""
    if FAULT_STATE["db_error"]:
        logger.error("Health check failed: Unable to connect to Database Cluster")
        return {"status": "unhealthy", "reason": "DB_CONNECTION_ERROR"}

    cpu_usage = psutil.cpu_percent()
    if cpu_usage > 95:
        logger.warning(f"Health check warning: High CPU usage {cpu_usage}%")
        return {"status": "unhealthy", "cpu": cpu_usage}
    return {"status": "healthy", "cpu": cpu_usage}

@app.post("/order")
async def create_order(item: str = "Standard Room"):
    """模拟下单接口，可能受到人为注入延迟的影响"""
    if FAULT_STATE["db_error"]:
        logger.error("Order creation failed: Database connection pool exhausted")
        raise HTTPException(status_code=500, detail="Internal Database Error")

    if FAULT_STATE["latency"] > 0:
        time.sleep(FAULT_STATE["latency"])
        logger.warning(f"Delayed order processing: {FAULT_STATE['latency']}s latency")

    order_id = random.randint(1000, 9999)
    logger.info(f"Order created: {order_id} for {item}")
    return {"order_id": order_id, "status": "pending"}

# --- 故障注入接口 (Fault Injection) ---

@app.post("/fault/db/start")
async def start_db_fault():
    """启动数据库连接故障"""
    FAULT_STATE["db_error"] = True
    logger.critical("FAULT INJECTED: Database connection pool exhausted (Simulated)")
    return {"message": "Database fault injected"}

@app.post("/fault/db/stop")
async def stop_db_fault():
    FAULT_STATE["db_error"] = False
    logger.info("FAULT REMOVED: Database connection restored")
    return {"message": "Database fault stopped"}

async def make_payment(order_id: int):
    """模拟支付接口，随机触发错误或内存异常"""
    if order_id % 7 == 0:
        logger.error(f"Payment failed for order {order_id}: Connection timeout to Bank Gateway")
        raise HTTPException(status_code=500, detail="Payment gateway connection error")
    
    logger.info(f"Payment successful for order {order_id}")
    return {"status": "paid", "order_id": order_id}

# --- 故障注入接口 (Fault Injection) ---

@app.post("/fault/cpu/start")
async def start_cpu_fault():
    """启动 CPU 飙升故障"""
    FAULT_STATE["cpu"] = True
    for _ in range(4): # 启动 4 个密集计算线程
        threading.Thread(target=cpu_intensive_task, daemon=True).start()
    logger.critical("FAULT INJECTED: CPU spike started")
    return {"message": "CPU fault injected"}

@app.post("/fault/cpu/stop")
async def stop_cpu_fault():
    FAULT_STATE["cpu"] = False
    logger.info("FAULT REMOVED: CPU spike stopped")
    return {"message": "CPU fault stopped"}

@app.post("/fault/latency/set")
async def set_latency(seconds: int):
    """设置固定延迟"""
    FAULT_STATE["latency"] = seconds
    logger.critical(f"FAULT INJECTED: Network latency set to {seconds}s")
    return {"message": f"Latency set to {seconds}s"}

@app.post("/fault/memory/leak")
async def inject_memory_leak():
    """触发一次内存大幅度占用（模拟泄漏）"""
    logger.critical("FAULT INJECTED: Memory leak simulated")
    large_list = [bytearray(1024 * 1024) for _ in range(100)] # 占用约 100MB
    FAULT_STATE["memory"].append(large_list)
    return {"message": "Memory leak injected (100MB)"}


# --- 后台任务：模拟真实业务负载和指标采集 ---
def metrics_collector():
    """后台线程：定期采集系统指标"""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            
            # 记录指标（保留最近60条）
            METRICS_DATA["cpu"].append({"timestamp": datetime.now().isoformat(), "value": cpu})
            METRICS_DATA["memory"].append({"timestamp": datetime.now().isoformat(), "value": memory})
            
            if len(METRICS_DATA["cpu"]) > 60:
                METRICS_DATA["cpu"].pop(0)
                METRICS_DATA["memory"].pop(0)
                
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
        time.sleep(2)


def business_simulator():
    """后台线程：模拟真实业务请求"""
    endpoints = ["/order", "/payment", "/query", "/health"]
    items = ["Standard Room", "Deluxe Room", "Suite", "Presidential Suite"]
    
    while True:
        try:
            endpoint = random.choice(endpoints)
            # 模拟请求延迟
            time.sleep(random.uniform(0.1, 1.5))
            
            # 模拟正常请求
            if random.random() > 0.05:  # 95% 成功率
                METRICS_DATA["requests"].append({
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": endpoint,
                    "status": 200,
                    "latency": random.uniform(10, 200)
                })
            else:
                METRICS_DATA["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "endpoint": endpoint,
                    "status": random.choice([500, 502, 503])
                })
                logger.warning(f"Request to {endpoint} failed")
            
            # 保持数据量合理
            for key in ["requests", "errors"]:
                if len(METRICS_DATA[key]) > 100:
                    METRICS_DATA[key].pop(0)
                    
        except Exception as e:
            logger.error(f"Business simulator error: {e}")
        time.sleep(random.uniform(0.5, 2))


@app.get("/metrics/realtime")
async def get_realtime_metrics():
    """获取实时指标"""
    return {
        "cpu": METRICS_DATA["cpu"][-10:] if METRICS_DATA["cpu"] else [],
        "memory": METRICS_DATA["memory"][-10:] if METRICS_DATA["memory"] else [],
        "requests_count": len(METRICS_DATA["requests"]),
        "errors_count": len(METRICS_DATA["errors"])
    }


# 启动后台任务
threading.Thread(target=metrics_collector, daemon=True, name="MetricsCollector").start()
threading.Thread(target=business_simulator, daemon=True, name="BusinessSimulator").start()
logger.info("Background tasks started: metrics collection and business simulation")

if __name__ == "__main__":
    import uvicorn
    # 服务运行在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
