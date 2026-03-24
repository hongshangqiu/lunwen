from fastapi import APIRouter, HTTPException
from app.schemas import MetricsSummaryRequest, MetricsSummaryResponseData
from app.services import summary_service

router = APIRouter()


@router.post("/metrics/summary", response_model=dict)
def get_metrics_summary(req: MetricsSummaryRequest):
    """
    获取指标摘要
    """
    try:
        result = summary_service.get_metrics_summary(
            service_name=req.serviceName,
            start_time=req.startTime,
            end_time=req.endTime,
            metrics=req.metrics
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
