"""
Evaluation API Router
提供实验评估的 API 接口
"""
from fastapi import APIRouter, HTTPException
from evaluation.experiments import (
    ComparativeEvaluator,
    run_comparative_experiments,
    get_all_scenes,
    get_scene_by_id
)

router = APIRouter()


@router.get("/evaluation/scenes", response_model=dict)
def get_evaluation_scenes():
    """获取所有测试场景"""
    scenes = get_all_scenes()
    return {
        "success": True,
        "data": [
            {
                "scene_id": s.scene_id,
                "scene_name": s.scene_name,
                "fault_type": s.fault_type.value,
                "difficulty": s.difficulty
            }
            for s in scenes
        ]
    }


@router.get("/evaluation/scenes/{scene_id}", response_model=dict)
def get_scene_detail(scene_id: str):
    """获取场景详情"""
    scene = get_scene_by_id(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    return {
        "success": True,
        "data": {
            "scene_id": scene.scene_id,
            "scene_name": scene.scene_name,
            "description": scene.description,
            "fault_type": scene.fault_type.value,
            "service": scene.service,
            "question": scene.question,
            "expected_root_cause": scene.expected_root_cause,
            "difficulty": scene.difficulty,
            "metrics": scene.metrics,
            "keywords": scene.keywords
        }
    }


@router.post("/evaluation/run", response_model=dict)
def run_evaluation():
    """运行对比实验"""
    try:
        evaluator = ComparativeEvaluator()
        results = evaluator.run_all_experiments()
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluation/run_single", response_model=dict)
def run_single_experiment(experiment_type: str, scene_id: str):
    """
    运行单个实验
    
    Args:
        experiment_type: 实验类型 (llm_only, rag_only, rag_realtime, full_method)
        scene_id: 场景 ID
    """
    from evaluation.experiments.evaluator import (
        LLMOnlyExperiment,
        RAGOnlyExperiment,
        RAGWithRealtimeExperiment,
        FullMethodExperiment
    )
    
    scene = get_scene_by_id(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    experiment_map = {
        "llm_only": LLMOnlyExperiment,
        "rag_only": RAGOnlyExperiment,
        "rag_realtime": RAGWithRealtimeExperiment,
        "full_method": FullMethodExperiment
    }
    
    if experiment_type not in experiment_map:
        raise HTTPException(status_code=400, detail="Invalid experiment type")
    
    try:
        experiment = experiment_map[experiment_type]()
        result = experiment.run(scene)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluation/results", response_model=dict)
def get_evaluation_results():
    """获取历史实验结果"""
    # TODO: 从数据库或文件加载历史结果
    return {
        "success": True,
        "data": {
            "message": "历史结果功能开发中"
        }
    }
