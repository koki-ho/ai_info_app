# AI情報収集アプリ 設計書

## 1. 概要

トピック(例: ハーネスエンジニアリング)を登録すると、関連する最新のブログ記事・ニュースをLLM+Web検索で収集し、URL付きで一覧表示するWebアプリケーション。収集はユーザーが欲しいタイミングで実行する(オンデマンド)。

特別機能として、履歴書(職務経歴)とキャリアの方向性を登録すると、その文脈に合わせたキャリアアップ関連の記事・ニュースも同様に収集・表示する。

### 要件整理

| # | 要件 | 実現方法 |
|---|------|---------|
| R1 | トピックの登録・管理 | Web UI + DB(topics テーブル) |
| R2 | 欲しいタイミングでの情報収集 | UI の「更新」ボタン → バックエンドで非同期実行 + 進捗ポーリング |
| R3 | 記事一覧の画面表示(URLへ遷移可能) | React フロントエンド |
| R4 | 履歴書・キャリア方向性の登録 | Web UI + DB(career_profile テーブル) |
| R5 | キャリア文脈に応じた情報収集 | 収集時にプロフィールをプロンプトに注入 |
| R6 | LLMの差し替え(Claude / Gemini 等) | プロバイダ抽象化レイヤ + 設定による切り替え |

### 非機能要件・将来想定

- 当面はローカル(WSL2)でのシングルユーザー利用
- 将来: マルチユーザー化、AWSへのデプロイ(§12参照)。この前提でDB・認証・構成を「移行しやすい形」にしておく

## 2. 技術選定

### バックエンド

| 項目 | 技術 | 選定理由 |
|------|------|---------|
| 言語/管理 | **Python 3.12 + uv** | LLM関連ライブラリが最も充実。uv で pyproject.toml ベースの高速・再現可能な依存管理 |
| フレームワーク | **FastAPI** | 非同期I/O(LLM呼び出しと相性が良い)、Pydanticによる型安全、OpenAPI自動生成 |
| ORM | **SQLAlchemy 2.0 + Alembic** | SQLite→PostgreSQL(AWS RDS)への移行がコード変更ほぼゼロ。Alembicでマイグレーション管理 |
| DB | **SQLite**(ローカル) | 単一ユーザーならサーバ不要。将来 PostgreSQL に差し替え |
| バリデーション | **Pydantic v2** | APIスキーマ・LLM出力のJSON検証を共通化 |
| LLM SDK | **anthropic**(デフォルト)、**google-genai**(差し替え用) | 各社公式SDK。§4の抽象化レイヤ越しに利用 |

### フロントエンド

| 項目 | 技術 | 選定理由 |
|------|------|---------|
| 管理 | **pnpm** | 高速・ディスク効率の良いパッケージ管理 |
| フレームワーク | **Vite + React 18 + TypeScript** | バックエンドが独立APIサーバなのでSPAで十分軽量。AWS移行時はS3+CloudFrontに静的配信できる |
| データ取得 | **TanStack Query** | ポーリング(収集進捗)・キャッシュ・再取得を宣言的に記述 |
| UI | **Tailwind CSS** | 軽量・カスタマイズ容易 |

### LLM(情報収集エンジン)

| プロバイダ | モデル | 検索手段 |
|-----------|--------|---------|
| **Anthropic(デフォルト)** | `claude-opus-4-8` | サーバーサイド Web検索ツール `web_search_20260209`(検索クエリ生成〜結果の取捨選択までモデルが実行。動的フィルタリング内蔵) |
| Google(差し替え) | Gemini 系 | Google Search グラウンディング |

検索API(SerpAPI等)やRSSクローラの自前実装は採用しない。トピックが「ハーネスエンジニアリング」のような自然言語で登録されるため、LLM+検索ツールが最も適合する。

## 3. アーキテクチャ

```
┌──── フロントエンド (Vite + React, pnpm) ────┐
│  /        … 記事フィード(トピック別タブ・キャリアタブ)│
│  /topics  … トピック管理                      │
│  /career  … 履歴書・キャリア方向性の登録        │
└───────────────┬──────────────────────────────┘
                │ REST (fetch / TanStack Query)
┌───────────────▼──── バックエンド (FastAPI, uv) ─────────────┐
│  routers/                                                    │
│   ├ topics.py  career.py  articles.py                        │
│   └ collect.py … POST /api/collect → BackgroundTask 起動     │
│                  GET  /api/runs/{id} → 進捗ポーリング          │
│  services/                                                   │
│   └ collector.py … 収集オーケストレーション(プロバイダ非依存)  │
│  llm/                          ← LLM抽象化レイヤ(§4)        │
│   ├ base.py      … ArticleCollector インターフェース          │
│   ├ anthropic_.py … Claude + web_search 実装                 │
│   ├ gemini_.py    … Gemini + Google Search 実装              │
│   └ factory.py    … 設定(env)から実装を選択                  │
└───────┬──────────────────────────┬───────────────────────────┘
        │ SQLAlchemy               │
 ┌──────▼──────┐          ┌────────▼────────┐
 │   SQLite    │          │ Claude API /     │
 │ (将来: RDS) │          │ Gemini API       │
 └─────────────┘          └─────────────────┘
```

収集は cron ではなく、UIの「更新」ボタン(全件 or トピック単位)から `POST /api/collect` を叩いて実行する。FastAPI の BackgroundTasks で非同期実行し、フロントは run の状態をポーリングして完了後にフィードを再取得する。

## 4. LLM抽象化レイヤ

プロバイダ差し替えの要。**「トピック/プロフィール + 既知URL を渡すと、記事リスト(共通スキーマ)が返る」** という1点だけをインターフェースとして固定し、検索ツールの使い方・pause処理などプロバイダ固有の事情は各実装に閉じ込める。

```python
# llm/base.py
from abc import ABC, abstractmethod
from datetime import date
from pydantic import BaseModel, HttpUrl

class CollectedArticle(BaseModel):
    title: str
    url: HttpUrl
    source: str | None = None
    published_at: date | None = None
    summary: str                    # 日本語2〜3文
    relevance: str | None = None    # キャリア収集時のみ

class CollectionRequest(BaseModel):
    kind: str                       # "topic" | "career"
    query_text: str                 # トピック名+補足、またはレジュメ+方向性
    known_urls: list[str]           # 重複除外用
    max_articles: int = 8

class ArticleCollector(ABC):
    @abstractmethod
    async def collect(self, req: CollectionRequest) -> list[CollectedArticle]: ...
```

```python
# llm/factory.py
from app.config import settings

def get_collector() -> ArticleCollector:
    match settings.llm_provider:        # 環境変数 LLM_PROVIDER
        case "anthropic":
            return AnthropicCollector(model=settings.llm_model)  # 既定: claude-opus-4-8
        case "gemini":
            return GeminiCollector(model=settings.llm_model)
        case _:
            raise ValueError(f"unknown provider: {settings.llm_provider}")
```

プロンプト(システム指示・出力JSONフォーマット)は `llm/prompts.py` にプロバイダ非依存で共通化し、各実装は「自社の検索ツールを有効にしてプロンプトを実行し、最終テキストからJSONを抽出して `CollectedArticle` に検証(Pydantic)」する責務だけを持つ。

### 4.1 Anthropic実装(デフォルト)

```python
# llm/anthropic_.py
import anthropic
from .base import ArticleCollector, CollectionRequest, CollectedArticle
from .prompts import build_system_prompt, build_user_prompt
from .parse import extract_articles_json

class AnthropicCollector(ArticleCollector):
    def __init__(self, model: str = "claude-opus-4-8"):
        self.client = anthropic.AsyncAnthropic()  # ANTHROPIC_API_KEY を環境変数から
        self.model = model

    async def collect(self, req: CollectionRequest) -> list[CollectedArticle]:
        tools = [{"type": "web_search_20260209", "name": "web_search",
                  "max_uses": req.max_articles}]
        messages = [{"role": "user", "content": build_user_prompt(req)}]

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=build_system_prompt(req.kind),
            tools=tools,
            messages=messages,
        )

        # サーバーサイドツールの反復上限到達時は assistant ターンを積んで再送・継続
        continuations = 0
        while response.stop_reason == "pause_turn" and continuations < 5:
            continuations += 1
            messages = [*messages, {"role": "assistant", "content": response.content}]
            response = await self.client.messages.create(
                model=self.model, max_tokens=16000,
                thinking={"type": "adaptive"},
                system=build_system_prompt(req.kind),
                tools=tools, messages=messages,
            )

        text = "".join(b.text for b in response.content if b.type == "text")
        return extract_articles_json(text)  # 末尾のJSON配列抽出 + Pydantic検証
```

実装上の注意:

- **構造化出力(`output_config.format`)は使わない。** Web検索結果には引用(citations)が付き、構造化出力は引用と非互換(400エラー)。最終テキストにJSON配列を出力させてパース+Pydantic検証する方式が、プロバイダ間で共通化しやすい点でも有利。
- **`pause_turn` ハンドリング必須**(Anthropic固有。抽象化レイヤの内側に隠蔽)。
- SDKが429/5xxを自動リトライ(既定2回)。

### 4.2 Gemini実装(差し替え)

`google-genai` SDK + Google Search グラウンディングで同じインターフェースを実装する。出力JSONフォーマットとパース処理(`extract_articles_json`)は共通のものを再利用。当初はスタブでもよく、必要になった時点で実装する。

### 4.3 プロンプト設計(共通)

**トピック収集:**

```text
あなたは技術情報のキュレーターです。
指定されたトピックについて、過去1週間以内に公開された質の高い
ブログ記事・ニュース・公式発表をWeb検索で探してください。

最後に必ず次のJSON配列**のみ**を出力(前置き・後書き禁止):
[{"title", "url", "source", "published_at" (YYYY-MM-DD or null), "summary" (日本語2〜3文)}]

ルール:
- 最大{max_articles}件。質を優先し、無理に件数を埋めない
- 一次情報(公式ブログ、論文、リリースノート)を優先
- 既知URLリストに含まれるものは除外
- 該当が無ければ [] を返す
```

**キャリア収集(特別機能):** 履歴書と方向性をそのままプロンプトに注入する。

```text
あなたはITエンジニアのキャリアアドバイザー兼キュレーターです。
以下の経歴とキャリアの方向性を持つエンジニアにとって「今読むべき」
記事・ニュースをWeb検索で探してください。観点:
- 目標の方向性で求められるスキル・技術トレンド
- 該当職種の採用動向・市場価値に関する情報
- 経歴とのギャップを埋める学習リソースや実践知見

# 経歴(履歴書より)
{resume_text}

# キャリアの方向性
{career_direction}

出力JSONには "relevance"(なぜこの人に関連するか1〜2文)を追加すること。
```

## 5. データモデル(SQLAlchemy / Alembic管理)

将来のマルチユーザー化を見据え、`user_id` カラムを最初から持たせておく(ローカル運用中は固定値 `1`)。

```python
class User(Base):                # 当面は seed で1レコードのみ
    id: int
    email: str | None
    created_at: datetime

class Topic(Base):
    id: int
    user_id: int                 # FK users.id
    name: str                    # 例: "ハーネスエンジニアリング"
    note: str | None             # 検索の補足コンテキスト
    enabled: bool = True
    created_at: datetime

class CareerProfile(Base):       # user_id でユニーク
    id: int
    user_id: int
    resume_text: str             # 履歴書・職務経歴(テキスト)
    career_direction: str        # 例: "MLエンジニアからAIプラットフォームのテックリードへ"
    enabled: bool = True
    updated_at: datetime

class Article(Base):
    id: int
    user_id: int
    topic_id: int | None         # null = キャリア収集分
    kind: str                    # "topic" | "career"
    title: str
    url: str                     # (user_id, url) でユニーク → 重複収集防止
    source: str | None
    published_at: date | None
    summary: str
    relevance: str | None        # キャリア分のみ
    is_read: bool = False
    collected_at: datetime

class CollectionRun(Base):
    id: int
    user_id: int
    scope: str                   # "all" | "topic:{id}" | "career"
    status: str                  # "running" | "success" | "partial" | "failed"
    detail: str | None           # 対象別の件数・エラー(JSON)
    started_at: datetime
    finished_at: datetime | None
```

## 6. 収集パイプライン(オンデマンド)

1. UIの「更新」ボタン → `POST /api/collect`(全件 / `topic_id` 指定 / `career` のみ)
2. 実行中の run が既にあれば 409 を返す(多重実行防止)
3. `CollectionRun` を `running` で作成し、run_id を即時レスポンス
4. BackgroundTask 内で対象ごとに:
   - 既知URL(そのトピックの直近200件)を取得
   - `factory.get_collector().collect(req)` を呼ぶ
   - 返却記事を `(user_id, url)` の upsert で保存(プロンプト除外+DB制約の二段構えで重複防止)
   - 対象単位の失敗はスキップして継続、`detail` に記録(最終 status は `partial`)
5. フロントは `GET /api/runs/{id}` を2〜3秒間隔でポーリングし、完了したらフィードを再取得

LLM呼び出しは `asyncio.Semaphore(2)` 程度で並列度を絞って実行(レートリミット対策)。

## 7. API設計

| Method | Path | 内容 |
|--------|------|------|
| GET | `/api/topics` | トピック一覧 |
| POST | `/api/topics` | 追加 `{name, note?}` |
| PATCH | `/api/topics/{id}` | 編集・有効/無効 |
| DELETE | `/api/topics/{id}` | 削除(記事もカスケード) |
| GET | `/api/career` | プロフィール取得 |
| PUT | `/api/career` | 登録・更新 `{resume_text, career_direction, enabled}` |
| GET | `/api/articles?kind=&topic_id=&unread_only=&page=` | 記事一覧(新しい順) |
| PATCH | `/api/articles/{id}` | 既読フラグ |
| POST | `/api/collect` | 収集実行 `{scope: "all" \| "topic" \| "career", topic_id?}` → `{run_id}`。実行中は409 |
| GET | `/api/runs/{id}` | run の状態・進捗 |
| GET | `/api/runs?limit=` | 収集履歴(最終更新日時の表示用) |

FastAPIのOpenAPIから `openapi-typescript` でフロントの型を生成し、スキーマのずれを防ぐ。

## 8. 画面設計

### `/` フィード(メイン)
- 上部: タブ(「すべて」「キャリア」+ トピック別)、最終更新日時、「更新」ボタン(全件/このタブのみ)
- 更新中はボタンをスピナー化し、runポーリングで完了検知 → フィード自動リロード
- 記事カード: タイトル(外部リンク `target="_blank"`)、媒体名、公開日、要約、(キャリア分は)関連性、既読マーク
- 新しい順・日付グルーピング

### `/topics` トピック管理
- 一覧 + 追加フォーム、有効/無効トグル、削除、トピック単位の「今すぐ収集」

### `/career` キャリア設定
- 履歴書テキストエリア、方向性テキストエリア、有効/無効トグル、保存

## 9. ディレクトリ構成(モノレポ)

```
ai_info_app/
├── backend/
│   ├── pyproject.toml            # uv 管理 (fastapi, sqlalchemy, alembic, anthropic, ...)
│   ├── uv.lock
│   ├── app/
│   │   ├── main.py               # FastAPI エントリポイント
│   │   ├── config.py             # pydantic-settings (LLM_PROVIDER, LLM_MODEL, DB URL, APIキー)
│   │   ├── db.py                 # engine / session
│   │   ├── models.py             # SQLAlchemy モデル
│   │   ├── schemas.py            # Pydantic スキーマ
│   │   ├── routers/
│   │   │   ├── topics.py  career.py  articles.py  collect.py
│   │   ├── services/
│   │   │   └── collector.py      # 収集オーケストレーション
│   │   └── llm/
│   │       ├── base.py  factory.py  prompts.py  parse.py
│   │       ├── anthropic_.py
│   │       └── gemini_.py
│   └── alembic/                  # マイグレーション
├── frontend/
│   ├── package.json              # pnpm 管理
│   ├── pnpm-lock.yaml
│   ├── vite.config.ts            # dev 時は /api を backend へ proxy
│   └── src/
│       ├── pages/  components/  api/(生成型 + fetch ラッパ)
├── docs/
│   └── DESIGN.md
└── README.md
```

ローカル起動:

```bash
# backend
cd backend && uv run fastapi dev app/main.py        # :8000
# frontend
cd frontend && pnpm dev                              # :5173 (/api → :8000 proxy)
```

## 10. コスト概算

- デフォルトモデル: `claude-opus-4-8`($5/M 入力・$25/M 出力)
- 1対象(トピック or キャリア)1回の収集 ≒ 入力10〜20Kトークン(検索結果込み)+ 出力2〜4K ≒ **$0.1〜0.2 程度**
- オンデマンド実行なので使った分だけ。例: トピック5件+キャリアを週3回全件更新 ≒ 月 **$10〜20 前後**
- 別途 Web検索ツールの検索回数課金あり(料金は https://platform.claude.com/docs/en/pricing 参照)。`max_uses` で上限制御
- コスト調整: `LLM_MODEL=claude-sonnet-4-6` に切替($3/$15)、`max_uses` 縮小、対象を絞った部分更新の活用

## 11. 実装ステップ

1. **基盤**: backend(uv + FastAPI + SQLAlchemy/Alembic + SQLite)、frontend(pnpm + Vite + React + Tailwind)の雛形、dev proxy 設定
2. **LLMレイヤ**: `llm/base.py` → `anthropic_.py` → `parse.py`。CLIから1トピックで動作確認(`uv run python -m app.llm.anthropic_ --topic "..."`)
3. **収集サービス + API**: collect/run エンドポイント、多重実行防止、upsert
4. **CRUD API**: topics / career / articles
5. **UI**: フィード(ポーリング含む)→ トピック管理 → キャリア設定
6. **特別機能**: キャリア収集のプロンプト調整・relevance 表示
7. **(任意)Gemini実装**: `gemini_.py` を追加し `LLM_PROVIDER=gemini` で切替確認

## 12. 拡張ロードマップ(マルチユーザー / AWS)

設計時点で仕込んでおくもの(本書反映済み):

- 全テーブルに `user_id`(ローカルでは固定値1)
- DBアクセスはSQLAlchemy経由 → 接続文字列の変更だけで PostgreSQL(RDS)へ移行可能
- 設定は環境変数(pydantic-settings)に集約 → AWSでは Secrets Manager / SSM Parameter Store に置換
- フロントはSPA → S3 + CloudFront に静的配信可能
- バックエンドはステートレス(収集状態はDBに永続化)→ コンテナ水平スケール可能

AWS移行時の構成案:

| 要素 | サービス |
|------|---------|
| フロントエンド | S3 + CloudFront |
| バックエンドAPI | ECS Fargate または App Runner(コンテナ化: `uv` ベースの Dockerfile) |
| DB | RDS for PostgreSQL(Alembicでそのままマイグレーション) |
| 認証(マルチユーザー化) | Amazon Cognito(JWTをFastAPI側で検証、`user_id` を請求元から解決) |
| 収集ジョブ | 当面はAPI内のBackgroundTaskで継続。負荷増なら SQS + ワーカー(ECS)へ分離。定期収集を復活させたい場合は EventBridge Scheduler → `POST /api/collect` |
| シークレット | Secrets Manager(各LLMのAPIキー) |
| ログ/監視 | CloudWatch Logs + run履歴テーブル |

マルチユーザー化の差分: Cognito認証ミドルウェア追加、`user_id=1` 固定の依存性(`get_current_user`)を実装し直すだけで、API・モデルの構造変更は不要。
