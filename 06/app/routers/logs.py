from fastapi import APIRouter, HTTPException
from app.schemas import LogsSummaryRequest
from app.services import summary_service

router = APIRouter()


@router.post("/logs/summary", response_model=dict)
def get_logs_summary(req: LogsSummaryRequest):
    """
    获取日志摘要
    """
    try:
        result = summary_service.get_logs_summary(
            service_name=req.serviceName,
            start_time=req.startTime,
            end_time=req.endTime,
            keywords=req.keywords,
            limit=req.limit
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
