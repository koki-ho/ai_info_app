"""収集オーケストレーション(docs/DESIGN.md §6)。

POST /api/collect のBackgroundTaskから呼ばれ、対象(有効トピック /
キャリアプロフィール)ごとにLLM収集を実行して記事をupsertする。
対象単位の失敗はスキップして継続し、runの detail にJSONで記録する。
"""

import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.llm.base import CollectionRequest
from app.llm.factory import get_collector
from app.models import Article, CareerProfile, CollectionRun, Topic, utcnow

logger = logging.getLogger(__name__)

KNOWN_URLS_LIMIT = 200  # プロンプトに注入する既知URLの上限(重複除外用)
MAX_ARTICLES_PER_TARGET = 8
LLM_CONCURRENCY = 2  # レートリミット対策(docs/DESIGN.md §6)


def _known_urls(db: Session, user_id: int, *, topic_id: int | None, kind: str) -> list[str]:
    stmt = (
        select(Article.url)
        .where(Article.user_id == user_id, Article.kind == kind)
        .order_by(Article.collected_at.desc())
        .limit(KNOWN_URLS_LIMIT)
    )
    if kind == "topic":
        stmt = stmt.where(Article.topic_id == topic_id)
    return list(db.scalars(stmt))


def _upsert_articles(
    db: Session,
    user_id: int,
    *,
    kind: str,
    topic_id: int | None,
    articles: list,
) -> int:
    """(user_id, url) で重複を防ぎつつ保存。新規保存件数を返す。"""
    inserted = 0
    for a in articles:
        existing = db.scalar(
            select(Article).where(Article.user_id == user_id, Article.url == a.url)
        )
        if existing is not None:
            # 既存記事は要約等を最新の収集結果で更新(既読フラグは維持)
            existing.title = a.title
            existing.source = a.source
            existing.published_at = a.published_at
            existing.summary = a.summary
            if a.relevance is not None:
                existing.relevance = a.relevance
            continue
        db.add(
            Article(
                user_id=user_id,
                topic_id=topic_id,
                kind=kind,
                title=a.title,
                url=a.url,
                source=a.source,
                published_at=a.published_at,
                summary=a.summary,
                relevance=a.relevance,
            )
        )
        inserted += 1
    db.commit()
    return inserted


def _build_targets(db: Session, user_id: int, scope: str) -> list[dict]:
    """scope("all" | "topic:{id}" | "career")から収集対象を列挙する。"""
    targets: list[dict] = []

    def topic_target(t: Topic) -> dict:
        query = t.name if not t.note else f"{t.name}\n補足: {t.note}"
        return {"label": f"topic:{t.id} {t.name}", "kind": "topic", "topic_id": t.id, "query": query}

    def career_target(p: CareerProfile) -> dict:
        query = (
            f"# 経歴(履歴書より)\n{p.resume_text}\n\n# キャリアの方向性\n{p.career_direction}"
        )
        return {"label": "career", "kind": "career", "topic_id": None, "query": query}

    if scope.startswith("topic:"):
        topic = db.get(Topic, int(scope.removeprefix("topic:")))
        if topic is not None and topic.user_id == user_id:
            targets.append(topic_target(topic))
        return targets

    if scope in ("all", "career"):
        profile = db.scalar(
            select(CareerProfile).where(
                CareerProfile.user_id == user_id, CareerProfile.enabled.is_(True)
            )
        )
        if profile is not None:
            targets.append(career_target(profile))
    if scope == "all":
        topics = db.scalars(
            select(Topic).where(Topic.user_id == user_id, Topic.enabled.is_(True))
        ).all()
        targets = [topic_target(t) for t in topics] + targets
    return targets


async def run_collection(run_id: int) -> None:
    """BackgroundTaskエントリポイント。run_idのCollectionRunを実行・完了させる。

    ここで例外を漏らすと run が "running" のまま残るため、想定外の失敗も
    含めて必ず run を完了状態にする。
    """
    try:
        await _run_collection(run_id)
    except Exception as e:  # 例: APIキー未設定でコレクタ生成に失敗
        logger.exception("収集run %s が異常終了", run_id)
        _finish_run(run_id, "failed", [{"error": str(e)}])


def _finish_run(run_id: int, status: str, results: list[dict]) -> None:
    with SessionLocal() as db:
        run = db.get(CollectionRun, run_id)
        if run is not None and run.status == "running":
            run.status = status
            run.detail = json.dumps(results, ensure_ascii=False)
            run.finished_at = utcnow()
            db.commit()


async def _run_collection(run_id: int) -> None:
    semaphore = asyncio.Semaphore(LLM_CONCURRENCY)
    collector = get_collector()

    with SessionLocal() as db:
        run = db.get(CollectionRun, run_id)
        if run is None:
            logger.error("CollectionRun %s が見つかりません", run_id)
            return
        user_id = run.user_id
        targets = _build_targets(db, user_id, run.scope)

    async def collect_target(target: dict) -> dict:
        async with semaphore:
            with SessionLocal() as db:
                known = _known_urls(
                    db, user_id, topic_id=target["topic_id"], kind=target["kind"]
                )
            req = CollectionRequest(
                kind=target["kind"],
                query_text=target["query"],
                known_urls=known,
                max_articles=MAX_ARTICLES_PER_TARGET,
            )
            articles = await collector.collect(req)
            with SessionLocal() as db:
                inserted = _upsert_articles(
                    db,
                    user_id,
                    kind=target["kind"],
                    topic_id=target["topic_id"],
                    articles=articles,
                )
            return {"target": target["label"], "collected": len(articles), "new": inserted}

    outcomes = await asyncio.gather(
        *(collect_target(t) for t in targets), return_exceptions=True
    )

    results: list[dict] = []
    failures = 0
    for target, outcome in zip(targets, outcomes):
        if isinstance(outcome, BaseException):
            failures += 1
            logger.error("収集失敗: %s", target["label"], exc_info=outcome)
            results.append({"target": target["label"], "error": str(outcome)})
        else:
            results.append(outcome)

    if not targets:
        status = "failed"
        results.append({"error": "収集対象がありません(有効なトピック/プロフィール無し)"})
    elif failures == 0:
        status = "success"
    elif failures == len(targets):
        status = "failed"
    else:
        status = "partial"

    _finish_run(run_id, status, results)
