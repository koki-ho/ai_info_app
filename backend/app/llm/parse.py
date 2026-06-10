"""最終テキストからJSON配列を抽出し CollectedArticle に検証(docs/DESIGN.md §4.1)。

構造化出力はWeb検索のcitationsと非互換(400)のためテキストJSONパース方式を採用。
プロンプトで「JSON配列のみ」を指示しているが、モデルが前置きやコードフェンスを
付けるケースに備え、テキスト末尾側から最初に見つかる妥当なJSON配列を採用する。
"""

import json
import logging

from pydantic import ValidationError

from app.llm.base import CollectedArticle

logger = logging.getLogger(__name__)


class ArticleParseError(ValueError):
    """最終テキストからJSON配列を抽出できなかった。"""


def _find_json_array(text: str) -> list:
    decoder = json.JSONDecoder()
    # 末尾側の '[' から順に試す(前置きテキストや途中の引用に含まれる '[' を回避)
    for i in range(len(text) - 1, -1, -1):
        if text[i] != "[":
            continue
        try:
            value, _ = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            return value
    raise ArticleParseError(
        f"レスポンスからJSON配列を抽出できません: {text[:200]!r}..."
    )


def extract_articles_json(text: str) -> list[CollectedArticle]:
    raw_items = _find_json_array(text)
    articles: list[CollectedArticle] = []
    for item in raw_items:
        if not isinstance(item, dict):
            logger.warning("記事でない要素をスキップ: %r", item)
            continue
        # "null" 文字列や空文字をNoneに正規化(モデル出力の揺れ対策)
        for key in ("source", "published_at", "relevance"):
            if item.get(key) in ("", "null", "None"):
                item[key] = None
        try:
            articles.append(CollectedArticle.model_validate(item))
        except ValidationError as e:
            logger.warning("検証に失敗した記事をスキップ: %r (%s)", item, e)
    return articles
