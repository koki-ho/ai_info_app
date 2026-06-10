from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"

    # LLM抽象化レイヤ(docs/DESIGN.md §4)
    llm_provider: str = "anthropic"  # "anthropic" | "gemini"
    llm_model: str = "claude-opus-4-8"

    # ローカル運用中はシングルユーザー固定(マルチユーザー化時に認証へ置換)
    default_user_id: int = 1


settings = Settings()
