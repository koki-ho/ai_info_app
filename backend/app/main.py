from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.routers import articles, career, collect, topics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ローカル運用中のシングルユーザーをseed(マルチユーザー化時に削除)
    with SessionLocal() as db:
        if db.get(User, settings.default_user_id) is None:
            db.add(User(id=settings.default_user_id))
            db.commit()
    yield


app = FastAPI(title="AI情報収集アプリ", lifespan=lifespan)

app.include_router(topics.router, prefix="/api")
app.include_router(career.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(collect.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "llm_provider": settings.llm_provider}
