from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TopicCreate(BaseModel):
    name: str
    note: str | None = None


class TopicUpdate(BaseModel):
    name: str | None = None
    note: str | None = None
    enabled: bool | None = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    note: str | None
    enabled: bool
    created_at: datetime


class CareerProfileIn(BaseModel):
    resume_text: str
    career_direction: str
    enabled: bool = True


class CareerProfileOut(CareerProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int | None
    kind: str
    title: str
    url: str
    source: str | None
    published_at: date | None
    summary: str
    relevance: str | None
    is_read: bool
    collected_at: datetime


class ArticleUpdate(BaseModel):
    is_read: bool


class CollectRequest(BaseModel):
    scope: str = "all"  # "all" | "topic" | "career"
    topic_id: int | None = None


class CollectAccepted(BaseModel):
    run_id: int


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scope: str
    status: str
    detail: str | None
    started_at: datetime
    finished_at: datetime | None
