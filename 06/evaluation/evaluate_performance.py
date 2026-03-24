import time
import json

def evaluate_system():
    """
    简化的系统性能评估脚本。
    对比人工排障与 AI 辅助排障的时间成本。
    """
    cases = [
        {"case": "CPU Spike", "manual_time_sec": 600, "ai_time_sec": 45, "is_accurate": True},
        {"case": "DB Connection Full", "manual_time_sec": 900, "ai_time_sec": 52, "is_accurate": True},
        {"case": "Memory Leak", "manual_time_sec": 1200, "ai_time_sec": 68, "is_accurate": True},
    ]
    
    print("=== AIOps 系统效能评估报告 ===")
    total_manual = sum(c['manual_time_sec'] for c in cases)
    total_ai = sum(c['ai_time_sec'] for c in cases)
    
    efficiency_gain = (total_manual - total_ai) / total_manual * 100
    
    print(f"总人工排障耗时: {total_manual}s")
    print(f"总 AI 辅助耗时: {total_ai}s")
    print(f"排障效率提升: {efficiency_gain:.2f}%")
    print(f"RCA 诊断准确率: {sum(c['is_accurate'] for c in cases)/len(cases)*100:.2f}%")

if __name__ == "__main__":
    evaluate_system()
