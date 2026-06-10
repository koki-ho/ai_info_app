from app.config import settings
from app.llm.base import ArticleCollector


def get_collector() -> ArticleCollector:
    match settings.llm_provider:
        case "anthropic":
            from app.llm.anthropic_ import AnthropicCollector

            return AnthropicCollector(model=settings.llm_model)
        case "gemini":
            from app.llm.gemini_ import GeminiCollector

            return GeminiCollector(model=settings.llm_model)
        case _:
            raise ValueError(f"unknown LLM provider: {settings.llm_provider}")
