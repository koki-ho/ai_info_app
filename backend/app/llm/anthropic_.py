"""Claude + サーバーサイドWeb検索ツールによる収集実装(docs/DESIGN.md §4.1)。

- 構造化出力はWeb検索のcitationsと非互換(400)のため、最終テキストの
  JSON配列をパースする方式(llm/parse.py)
- pause_turn(サーバーサイドツールの反復上限)はこの実装の内側で継続処理する
- 429/5xx はSDKが自動リトライ(既定2回)
"""

import anthropic

from app.llm.base import ArticleCollector, CollectedArticle, CollectionRequest
from app.llm.parse import extract_articles_json
from app.llm.prompts import build_system_prompt, build_user_prompt

_MAX_CONTINUATIONS = 5


class AnthropicCollector(ArticleCollector):
    def __init__(self, model: str = "claude-opus-4-8"):
        self.client = anthropic.AsyncAnthropic()  # ANTHROPIC_API_KEY を環境変数から
        self.model = model

    async def collect(self, req: CollectionRequest) -> list[CollectedArticle]:
        system = build_system_prompt(req.kind)
        tools = [
            {
                "type": "web_search_20260209",
                "name": "web_search",
                "max_uses": req.max_articles,
            }
        ]
        messages: list[dict] = [{"role": "user", "content": build_user_prompt(req)}]

        response = await self._create(system, tools, messages)

        # サーバーサイドツールの反復上限到達時は assistant ターンを積んで再送・継続
        continuations = 0
        while response.stop_reason == "pause_turn" and continuations < _MAX_CONTINUATIONS:
            continuations += 1
            messages = [*messages, {"role": "assistant", "content": response.content}]
            response = await self._create(system, tools, messages)

        text = "".join(b.text for b in response.content if b.type == "text")
        return extract_articles_json(text)

    async def _create(self, system: str, tools: list[dict], messages: list[dict]):
        return await self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=system,
            tools=tools,
            messages=messages,
        )


def _cli() -> None:
    """1トピックでの動作確認用CLI: uv run python -m app.llm.anthropic_ --topic "...\""""
    import argparse
    import asyncio

    from app.config import settings

    parser = argparse.ArgumentParser(description="AnthropicCollector 動作確認")
    parser.add_argument("--topic", required=True, help="収集するトピック名")
    parser.add_argument("--max-articles", type=int, default=5)
    parser.add_argument("--model", default=settings.llm_model)
    args = parser.parse_args()

    req = CollectionRequest(
        kind="topic",
        query_text=args.topic,
        known_urls=[],
        max_articles=args.max_articles,
    )
    articles = asyncio.run(AnthropicCollector(model=args.model).collect(req))
    for a in articles:
        print(a.model_dump_json(indent=2))
    print(f"--- {len(articles)} 件")


if __name__ == "__main__":
    _cli()
