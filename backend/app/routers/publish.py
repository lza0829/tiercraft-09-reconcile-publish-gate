from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import pipeline

router = APIRouter(tags=["汇总发布"])


class PublishBody(BaseModel):
    domain_id: int = Field(..., description="主题域编号")


@router.get("/publish")
def list_publish(domain_id: int | None = None):
    return pipeline.list_publish(domain_id)


@router.post("/publish")
def publish(body: PublishBody):
    # 无论成功或拒绝都返回本次发布记录；拒绝时记录内含原因，且发布区不被触碰
    try:
        return pipeline.publish_summary(body.domain_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
