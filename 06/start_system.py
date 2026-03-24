import subprocess
import time
import os
import sys

def run_command(command, is_background=False, cwd=None):
    """运行 shell 命令"""
    if is_background:
        return subprocess.Popen(command, shell=True, cwd=cwd)
    else:
        return subprocess.run(command, shell=True, cwd=cwd)

def check_and_install_deps(deps: list) -> bool:
    """
    检查依赖是否已安装，只安装缺失的包
    返回: 是否进行了安装操作
    """
    missing_deps = []
    for dep in deps:
        # 处理包名，去除版本号
        package_name = dep.split('>')[0].split('=')[0].split('<')[0]
        try:
            __import__(package_name)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"发现缺失依赖: {', '.join(missing_deps)}")
        print("正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q"] + missing_deps)
            return True
        except Exception as e:
            print(f"安装失败: {e}")
            return False
    else:
        print("✓ 所有依赖已就绪")
        return False


def main():
    print("="*60)
    print("🚀 AIOps-LLM-RAG 智能运维系统 - 一键启动工具")
    print("="*60)

    # 获取当前项目的根目录
    project_root = os.path.dirname(os.path.abspath(__file__))

    # 1. 检查并安装依赖
    print("\n[1/4] 正在检查必要依赖...")
    deps = ["streamlit", "fastapi", "uvicorn", "requests", "python-dotenv", "openai", "pydantic", "psutil", "pandas"]
    check_and_install_deps(deps)

    # 2. 启动受控微服务 (Demo Service, 端口 8000)
    print("[2/4] 正在启动受控微服务 (HotelService, 端口 8000)...")
    demo_process = run_command(
        f"{sys.executable} app/demo_service/main.py", 
        is_background=True,
        cwd=project_root
    )
    time.sleep(2)

    # 3. 启动后端 API 服务 (FastAPI, 端口 8001)
    print("[3/4] 正在启动后端分析服务 (FastAPI, 端口 8001)...")
    # 使用 -m app.main 启动，确保导入路径正确
    backend_process = run_command(
        f"{sys.executable} -m app.main", 
        is_background=True,
        cwd=project_root
    )
    time.sleep(3)

    # 4. 启动 Web 可视化界面 (Streamlit, 端口 8501)
    print("[4/4] 正在启动可视化看板 (Streamlit, 端口 8501)...")
    try:
        # Streamlit 运行在当前进程，按 Ctrl+C 停止所有服务
        run_command(
            f"streamlit run frontend/streamlit_app.py", 
            cwd=project_root
        )
    except KeyboardInterrupt:
        print("\n正在关闭系统...")
        backend_process.terminate()
        demo_process.terminate()
        print("已退出。")

if __name__ == "__main__":
    main()
