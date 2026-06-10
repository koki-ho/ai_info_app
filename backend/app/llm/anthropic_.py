# TODO(ステップ2): Claude + web_search_20260209 実装(docs/DESIGN.md §4.1)
# - AsyncAnthropic / thinking={"type": "adaptive"} / pause_turn 継続処理(上限5回)
# - CLI動作確認: uv run python -m app.llm.anthropic_ --topic "..."

from app.llm.base import ArticleCollector, CollectedArticle, CollectionRequest


class AnthropicCollector(ArticleCollector):
    def __init__(self, model: str = "claude-opus-4-8"):
        self.model = model

    async def collect(self, req: CollectionRequest) -> list[CollectedArticle]:
        raise NotImplementedError
