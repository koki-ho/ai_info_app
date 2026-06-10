from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Topic
from app.schemas import TopicCreate, TopicOut, TopicUpdate

router = APIRouter(tags=["topics"])


def _get_topic(db: Session, topic_id: int) -> Topic:
    topic = db.get(Topic, topic_id)
    if topic is None or topic.user_id != settings.default_user_id:
        raise HTTPException(status_code=404, detail="topic not found")
    return topic


@router.get("/topics", response_model=list[TopicOut])
def list_topics(db: Session = Depends(get_db)):
    return db.scalars(
        select(Topic)
        .where(Topic.user_id == settings.default_user_id)
        .order_by(Topic.created_at)
    ).all()


@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(body: TopicCreate, db: Session = Depends(get_db)):
    topic = Topic(user_id=settings.default_user_id, name=body.name, note=body.note)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.patch("/topics/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, body: TopicUpdate, db: Session = Depends(get_db)):
    topic = _get_topic(db, topic_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/topics/{topic_id}", status_code=204)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = _get_topic(db, topic_id)
    db.delete(topic)  # 記事は relationship の cascade で削除
    db.commit()
