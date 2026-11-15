from fastapi import APIRouter, HTTPException, Query

from app.services import pipeline

router = APIRouter(tags=["分层"])


@router.get("/layers/counts")
def counts(domain_id: int | None = Query(default=None)):
    return pipeline.layer_counts(domain_id)


@router.get("/layers/{layer}")
def list_layer(
    layer: str,
    domain_id: int | None = Query(default=None),
    state: str = Query(default="draft", description="汇总层状态：draft/草稿 或 published/已发布"),
):
    mapping = {"paste": "paste", "detail": "detail", "summary": "summary",
               "贴源": "paste", "明细": "detail", "汇总": "summary"}
    key = mapping.get(layer)
    if not key:
        raise HTTPException(status_code=400, detail="分层只能是贴源/明细/汇总")
    if key == "summary":
        # 草稿与已发布分表隔离查询：已发布只读发布副本，绝不回读草稿表
        if state in ("published", "已发布"):
            key = "summary_published"
        elif state not in ("draft", "草稿"):
            raise HTTPException(status_code=400, detail="汇总状态只能是草稿或已发布")
    try:
        return pipeline.layer_rows(key, domain_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
