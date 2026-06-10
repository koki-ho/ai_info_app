"""LLM抽象化レイヤのインターフェース(docs/DESIGN.md §4)。

「収集リクエスト → 共通スキーマの記事リスト」の1点だけを契約として固定し、
検索ツールの使い方・pause処理などプロバイダ固有の事情は各実装に閉じ込める。
"""

from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel, HttpUrl


class CollectedArticle(BaseModel):
    title: str
    url: HttpUrl
    source: str | None = None
    published_at: date | None = None
    summary: str  # 日本語2〜3文
    relevance: str | None = None  # キャリア収集時のみ


class CollectionRequest(BaseModel):
    kind: str  # "topic" | "career"
    query_text: str  # トピック名+補足、またはレジュメ+方向性
    known_urls: list[str]  # 重複除外用
    max_articles: int = 8


class ArticleCollector(ABC):
    @abstractmethod
    async def collect(self, req: CollectionRequest) -> list[CollectedArticle]: ...
