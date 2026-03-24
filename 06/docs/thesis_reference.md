# 论文图表与伪代码参考

本文档汇总了 LLM-Ops Copilot 系统中可直接引用到论文的图表数据、伪代码和实验结果。

---

## 图 3.1: 系统整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LLM-Ops Copilot 系统架构                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
│    │   用户界面   │     │   知识库    │     │  数据源     │        │
│    │  (Streamlit) │     │  (ChromaDB) │     │            │        │
│    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘        │
│           │                  │                  │                 │
│           └──────────────────┼──────────────────┘                 │
│                              ▼                                      │
│                    ┌─────────────────┐                             │
│                    │   API 网关      │                             │
│                    │   (FastAPI)     │                             │
│                    └────────┬────────┘                             │
│                             │                                       │
│    ┌────────────────────────┼────────────────────────┐             │
│    │                        ▼                        │             │
│    │   ┌─────────────────────────────────────┐      │             │
│    │   │         RAG Pipeline                 │      │             │
│    │   │  ┌─────────┐  ┌─────────┐  ┌─────┐ │      │             │
│    │   │  │ 证据融合 │  │ RCA引擎 │  │Prompt│ │      │             │
│    │   │  └─────────┘  └─────────┘  └─────┘ │      │             │
│    │   └─────────────────────────────────────┘      │             │
│    │                        │                        │             │
│    └────────────────────────┼────────────────────────┘             │
│                             ▼                                      │
│                    ┌─────────────────┐                             │
│                    │   LLM 服务      │                             │
│                    │ (GPT/Claude)    │                             │
│                    └─────────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 图 3.2: RAG 检索流程图

```
                    开始
                      │
                      ▼
            ┌─────────────────┐
            │ 接收自然语言查询  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ 向量编码查询文本  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ ChromaDB 检索   │
            │ Top-K 相似片段  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ 元数据过滤      │
            │ (可选: 服务/类型) │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ 结果排序与格式化  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ 返回知识块列表   │
            └────────┬────────┘
                     │
                     ▼
                    结束
```

**对应代码**: `app/services/knowledge_service.py` - `KnowledgeService.retrieve()`

---

## 图 3.3: 多源数据融合流程图

```
  用户问题              指标摘要              日志摘要
      │                   │                    │
      └───────────────────┼────────────────────┘
                          ▼
              ┌───────────────────────┐
              │     证据融合器         │
              │   EvidenceBuilder     │
              └───────────┬───────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
    ┌───────────┐  ┌───────────┐  ┌───────────┐
    │异常指标提取│  │严重程度评估│  │上下文构建 │
    └───────────┘  └───────────┘  └───────────┘
            │             │             │
            └─────────────┼─────────────┘
                          ▼
              ┌───────────────────────┐
              │   AnalysisContext     │
              │   统一分析上下文       │
              └───────────────────────┘
```

**对应代码**: `app/core/evidence_builder.py` - `EvidenceBuilder.build()`

---

## 图 3.4: RCA 推理流程图

```
           AnalysisContext
                 │
                 ▼
        ┌────────────────┐
        │  Prompt 渲染    │
        │ (上下文→文本)    │
        └───────┬────────┘
                ▼
        ┌────────────────┐
        │  LLM 调用      │
        │ (结构化生成)    │
        └───────┬────────┘
                ▼
        ┌────────────────┐
        │ JSON 解析      │
        │ 结果验证       │
        └───────┬────────┘
                ▼
        ┌────────────────┐
        │ RCAResult      │
        │ 结构化结果      │
        └────────────────┘
```

**对应代码**: `app/services/rca_engine.py` - `RCAEngine.analyze()`

---

## Algorithm 1: RAG 检索算法

```python
# 详见 app/services/knowledge_service.py
def retrieve(query, service=None, fault_type=None, top_k=3):
    # 1. 构建过滤条件
    filters = {}
    if service:
        filters["service_name"] = service
    if fault_type:
        filters["fault_type"] = fault_type
    
    # 2. 向量检索
    results = vector_store.search(
        query=query,
        top_k=top_k,
        filters=filters if filters else None
    )
    
    # 3. 格式化结果
    return _format_results(results)
```

---

## Algorithm 2: RCA 推理算法

```python
# 详见 app/services/rca_engine.py
def analyze(context):
    # 1. 构建结构化 Prompt
    prompt = build_rca_prompt(context_dict=context)
    
    # 2. 调用 LLM
    response = llm.call(prompt, system_prompt=SYSTEM_PROMPT)
    
    # 3. 解析 JSON 结果
    result = _parse_result(response)
    
    # 4. 构建 RCAResult
    return RCAResult(**result)
```

---

## Algorithm 3: 对比实验算法

```python
# 详见 evaluation/experiments/evaluator.py
def run_comparative_experiments(scenes, experiments):
    results = []
    
    for scene in scenes:
        for exp in experiments:
            # 运行实验
            result = exp.run(scene)
            
            # 评估结果
            metrics = evaluate(result, scene.ground_truth)
            
            results.append({
                "experiment": exp.name,
                "scene": scene.scene_id,
                "metrics": metrics
            })
    
    # 聚合结果
    return aggregate_results(results)
```

---

## 实验结果模板 (表 4.1, 4.2)

### 表 4.1: 根因定位准确率对比

| 实验方案 | 场景数 | 正确数 | 准确率 |
|---------|-------|-------|--------|
| LLM-Only | 7 | - | - |
| RAG-Only | 7 | - | - |
| RAG+Realtime | 7 | - | - |
| Full-Method | 7 | - | - |

### 表 4.2: 响应时间对比

| 实验方案 | 平均响应时间(s) | P95响应时间(s) | 最大响应时间(s) |
|---------|----------------|----------------|----------------|
| LLM-Only | - | - | - |
| RAG-Only | - | - | - |
| RAG+Realtime | - | - | - |
| Full-Method | - | - | - |

---

## 评估指标定义

| 指标名称 | 计算方式 | 说明 |
|---------|---------|------|
| RootCauseAccuracy | 正确预测数 / 总场景数 | 核心指标 |
| Top3Accuracy | Top3含正确根因的比例 | 召回指标 |
| ResponseTime | API 响应耗时 | 性能指标 |
| EvidenceCoverage | 覆盖正确证据数/总证据数 | 完整性 |
| SuggestionValidity | 有效建议数/总建议数 | 可操作性 |

---

## 模块引用索引

| 论文章节 | 对应模块 | 文件路径 |
|---------|---------|---------|
| 3.1 | 向量数据库封装 | `app/services/vector_store.py` |
| 3.1 | 知识检索服务 | `app/services/knowledge_service.py` |
| 3.2 | 证据融合器 | `app/core/evidence_builder.py` |
| 3.2 | 日志服务 | `app/services/log_service.py` |
| 3.2 | 指标服务 | `app/services/prometheus_service.py` |
| 3.3 | RCA 推理引擎 | `app/services/rca_engine.py` |
| 3.3 | Prompt 模板 | `app/core/prompts.py` |
| 3.4 | RAG 管道 | `app/services/rag_pipeline.py` |
| 4.3 | 对比实验 | `evaluation/experiments/` |
| 5 | 原型界面 | `frontend/streamlit_app.py` |
