# TODO(ステップ7・任意): Gemini + Google Search グラウンディング実装(docs/DESIGN.md §4.2)

from app.llm.base import ArticleCollector, CollectedArticle, CollectionRequest


class GeminiCollector(ArticleCollector):
    def __init__(self, model: str):
        self.model = model

    async def collect(self, req: CollectionRequest) -> list[CollectedArticle]:
        raise NotImplementedError
