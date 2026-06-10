# TODO(ステップ2): 最終テキストからJSON配列を抽出し CollectedArticle に検証(docs/DESIGN.md §4.1)
# 構造化出力はWeb検索のcitationsと非互換(400)のためテキストJSONパース方式を採用

from app.llm.base import CollectedArticle


def extract_articles_json(text: str) -> list[CollectedArticle]:
    raise NotImplementedError
