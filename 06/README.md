# LLM-Ops Copilot 智能运维分析与自愈系统

本项目是"基于大模型的软件运维方法"毕业设计的核心 Demo 演示系统。它通过集成实时监控指标、应用日志以及运维知识库（RAG），利用大模型实现故障的闭环诊断与自愈。

## 核心功能

1. **故障注入**：模拟 CPU 飙升、数据库连接耗尽、网络延迟等真实故障场景。
2. **多源数据融合**：实时采集受控服务的指标与日志，自动生成分析摘要。
3. **RAG 知识增强**：根据故障特征，从运维知识库中检索相关的 SOP 手册。
4. **智能根因分析 (RCA)**：大模型基于多源上下文，给出精准的故障定位与解释。
5. **自动化自愈 (Self-Healing)**：AI 生成对应的修复脚本，支持一键审批并执行。
6. **对比实验评估**：四组对照实验，量化评估不同方案的效果。

## 系统架构

- **受控微服务 (`app/demo_service/`)**: 模拟真实业务应用，暴露故障注入接口。 (Port: 8000)
- **分析后端 (`app/`)**: 基于 FastAPI 构建的 AIOps 核心，处理 RAG 检索、指标分析与 LLM 调用。 (Port: 8001)
- **前端 UI (`frontend/`)**: 基于 Streamlit 构建的可视化看板，提供交互式运维体验。 (Port: 8501)
- **向量数据库**: 基于 ChromaDB 的知识向量化存储
- **实验评估框架**: 四组对照实验，验证方案有效性

## 核心模块

| 模块 | 说明 | 论文对应章节 |
|------|------|-------------|
| `vector_store.py` | 向量数据库封装 | 3.1 |
| `knowledge_service.py` | RAG 知识检索服务 | 3.1 |
| `evidence_builder.py` | 多源数据融合 | 3.2 |
| `rca_engine.py` | RCA 结构化推理引擎 | 3.3 |
| `rag_pipeline.py` | 端到端 RAG 管道 | 3.4 |
| `prompts.py` | Prompt 模板设计 | 3.3 |
| `experiments/` | 对比实验框架 | 4.3 |

## 快速启动

1. **配置环境**：在 `.env` 文件中填写您的 LLM API Key (如 OpenAI 或 Qwen)。

2. **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

3. **向量化知识库**：
    ```bash
    python scripts/ingest_knowledge.py
    ```

4. **启动系统**：
    ```bash
    python start_system.py
    ```
    启动后，浏览器将自动打开 Streamlit 页面。

## 使用流程

1. 在左侧面板点击 **"注入故障"** 按钮。
2. 选择要分析的场景或输入自然语言问题。
3. 点击 **"执行 RCA 分析"**。
4. 查看诊断结论、置信度和修复建议。
5. 可选：点击 **"执行自愈脚本"** 恢复系统。

## 对比实验

系统支持四组对照实验：

| 实验组 | RAG | 实时指标 | 实时日志 | 结构化 Prompt |
|--------|-----|----------|----------|---------------|
| LLM-Only | ✗ | ✗ | ✗ | ✗ |
| RAG-Only | ✓ | ✗ | ✗ | ✗ |
| RAG+Realtime | ✓ | ✓ | ✓ | ✗ |
| Full-Method | ✓ | ✓ | ✓ | ✓ |

运行实验：
```python
from evaluation.experiments import run_comparative_experiments
results = run_comparative_experiments()
```

## 项目结构

```
06/
├── app/
│   ├── main.py              # 后端 API 入口
│   ├── config.py            # 系统配置
│   ├── demo_service/        # 受控微服务 (Target App)
│   ├── routers/             # API 路由
│   │   ├── analyze.py       # RCA 分析接口
│   │   ├── knowledge.py     # 知识库接口
│   │   └── evaluation.py    # 实验评估接口
│   ├── services/            # 核心逻辑
│   │   ├── vector_store.py  # 向量数据库
│   │   ├── knowledge_service.py  # RAG 服务
│   │   ├── rca_engine.py    # RCA 引擎
│   │   └── rag_pipeline.py  # RAG 管道
│   └── core/                # 核心模块
│       ├── prompts.py       # Prompt 模板
│       └── evidence_builder.py  # 证据融合
├── data/
│   ├── scenes.json          # 预设演示场景
│   ├── logs/                # 实时日志存放
│   └── docs/                # 原始知识库文档
├── evaluation/
│   └── experiments/         # 对比实验
│       ├── test_scenes.py   # 测试场景
│       └── evaluator.py     # 评估器
├── frontend/
│   └── streamlit_app.py     # 可视化 UI
├── scripts/
│   └── ingest_knowledge.py  # 知识向量化脚本
├── docs/
│   └── thesis_reference.md  # 论文参考
├── vector_store/            # 向量数据库
├── start_system.py          # 一键启动脚本
└── requirements.txt         # 依赖清单
```

## 论文支撑

详见 `docs/thesis_reference.md`，包含：

- 系统架构图
- RAG 检索流程图
- 多源数据融合流程图
- RCA 推理流程图
- 伪代码（Algorithm 1-3）
- 实验结果模板
- 评估指标定义
- 模块引用索引
