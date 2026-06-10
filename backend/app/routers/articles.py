from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Article
from app.schemas import ArticleOut, ArticleUpdate

router = APIRouter(tags=["articles"])

PAGE_SIZE = 50


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    kind: str | None = Query(None, pattern="^(topic|career)$"),
    topic_id: int | None = None,
    unread_only: bool = False,
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    stmt = select(Article).where(Article.user_id == settings.default_user_id)
    if kind is not None:
        stmt = stmt.where(Article.kind == kind)
    if topic_id is not None:
        stmt = stmt.where(Article.topic_id == topic_id)
    if unread_only:
        stmt = stmt.where(Article.is_read.is_(False))
    stmt = (
        # 公開日が新しい順(公開日不明は末尾)→ 収集日時の新しい順
        stmt.order_by(
            Article.published_at.desc().nulls_last(),
            Article.collected_at.desc(),
            Article.id.desc(),
        )
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )
    return db.scalars(stmt).all()


@router.patch("/articles/{article_id}", response_model=ArticleOut)
def update_article(article_id: int, body: ArticleUpdate, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if article is None or article.user_id != settings.default_user_id:
        raise HTTPException(status_code=404, detail="article not found")
    article.is_read = body.is_read
    db.commit()
    db.refresh(article)
    return article
