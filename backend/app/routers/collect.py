from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import CollectionRun, Topic
from app.schemas import CollectAccepted, CollectRequest, RunOut
from app.services.collector import run_collection

router = APIRouter(tags=["collect"])


@router.post("/collect", response_model=CollectAccepted, status_code=202)
def start_collect(
    body: CollectRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # 多重実行防止(docs/DESIGN.md §6)
    running = db.scalar(
        select(CollectionRun).where(
            CollectionRun.user_id == settings.default_user_id,
            CollectionRun.status == "running",
        )
    )
    if running is not None:
        raise HTTPException(
            status_code=409, detail=f"collection already running (run_id={running.id})"
        )

    match body.scope:
        case "all" | "career":
            scope = body.scope
        case "topic":
            if body.topic_id is None:
                raise HTTPException(status_code=422, detail="topic_id is required")
            topic = db.get(Topic, body.topic_id)
            if topic is None or topic.user_id != settings.default_user_id:
                raise HTTPException(status_code=404, detail="topic not found")
            scope = f"topic:{body.topic_id}"
        case _:
            raise HTTPException(status_code=422, detail=f"unknown scope: {body.scope}")

    run = CollectionRun(user_id=settings.default_user_id, scope=scope, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(run_collection, run.id)
    return CollectAccepted(run_id=run.id)


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(CollectionRun, run_id)
    if run is None or run.user_id != settings.default_user_id:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@router.get("/runs", response_model=list[RunOut])
def list_runs(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return db.scalars(
        select(CollectionRun)
        .where(CollectionRun.user_id == settings.default_user_id)
        .order_by(CollectionRun.started_at.desc(), CollectionRun.id.desc())
        .limit(limit)
    ).all()
