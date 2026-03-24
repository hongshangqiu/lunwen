import json
import os
from pathlib import Path
from typing import List, Optional
from app.config import DATA_DIR


def load_scenes() -> List[dict]:
    """
    加载所有预设场景配置
    """
    scenes_file = DATA_DIR / "scenes.json"
    if not scenes_file.exists():
        return []
    
    with open(scenes_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_scene_by_id(scene_id: str) -> Optional[dict]:
    """
    根据场景 ID 获取场景详情
    """
    scenes = load_scenes()
    for scene in scenes:
        if scene.get("sceneId") == scene_id:
            return scene
    return None


def get_scene_list() -> List[dict]:
    """
    获取场景列表（用于前端下拉框）
    """
    scenes = load_scenes()
    return [
        {
            "sceneId": s.get("sceneId"),
            "sceneName": s.get("sceneName"),
            "serviceName": s.get("serviceName")
        }
        for s in scenes
    ]
