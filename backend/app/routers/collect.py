from fastapi import APIRouter

router = APIRouter(tags=["collect"])

# TODO(ステップ3): POST /collect(409多重実行防止)、GET /runs/{id}, GET /runs を実装(docs/DESIGN.md §6, §7)
