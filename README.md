# AI情報収集アプリ

トピックや履歴書・キャリアの方向性を登録すると、LLM + Web検索で関連する最新のブログ記事・ニュースをオンデマンドに収集して表示するアプリケーション。

設計の詳細は [docs/DESIGN.md](docs/DESIGN.md) を参照。

## 構成

- `backend/` … FastAPI + SQLAlchemy/Alembic + SQLite(uv 管理、Python 3.12)
- `frontend/` … Vite + React + TypeScript + Tailwind CSS(pnpm 管理)

## セットアップ

```bash
# backend
cd backend
cp .env.example .env          # ANTHROPIC_API_KEY 等を設定
uv sync
uv run alembic upgrade head   # DB作成(./data/app.db)

# frontend
cd frontend
pnpm install
```

## ローカル起動

```bash
# backend (:8000)
cd backend && uv run fastapi dev app/main.py

# frontend (:5173 — /api は :8000 へプロキシ)
cd frontend && pnpm dev
```

http://localhost:5173 を開く。APIドキュメントは http://localhost:8000/docs 。

## LLMプロバイダの切り替え

`backend/.env` の `LLM_PROVIDER`(`anthropic` | `gemini`)と `LLM_MODEL` で切り替え(docs/DESIGN.md §4)。
