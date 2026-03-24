from fastapi import APIRouter, HTTPException
from app.schemas import SceneItem, SceneDetail
from app.services import scene_service

router = APIRouter()


@router.get("/scenes", response_model=dict)
def get_scenes():
    """
    获取场景列表
    """
    scenes = scene_service.get_scene_list()
    return {
        "success": True,
        "data": scenes
    }


@router.get("/scenes/{scene_id}", response_model=dict)
def get_scene_detail(scene_id: str):
    """
    获取单个场景详情
    """
    scene = scene_service.get_scene_by_id(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    return {
        "success": True,
        "data": scene
    }
