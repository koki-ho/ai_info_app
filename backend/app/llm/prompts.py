"""プロバイダ非依存のプロンプト(docs/DESIGN.md §4.3)。

各実装は「自社の検索ツールを有効にしてこのプロンプトを実行し、
最終テキストからJSON配列を抽出して検証」する責務だけを持つ。
"""

from app.llm.base import CollectionRequest

_JSON_FORMAT = """\
最後に必ず次の形式のJSON配列**のみ**を出力してください(前置き・後書き・コードフェンス禁止):
[{"title": "...", "url": "...", "source": "...", "published_at": "YYYY-MM-DD または null", "summary": "日本語2〜3文の要約"}]
"""

_TOPIC_SYSTEM = f"""\
あなたは技術情報のキュレーターです。
指定されたトピックについて、過去1週間以内に公開された質の高い
ブログ記事・ニュース・公式発表をWeb検索で探してください。

{_JSON_FORMAT}
ルール:
- 指定された最大件数まで。質を優先し、無理に件数を埋めない
- 一次情報(公式ブログ、論文、リリースノート)を優先
- 既知URLリストに含まれるものは除外
- 該当が無ければ [] を返す
"""

_CAREER_SYSTEM = f"""\
あなたはITエンジニアのキャリアアドバイザー兼キュレーターです。
提示される経歴とキャリアの方向性を持つエンジニアにとって「今読むべき」
記事・ニュースをWeb検索で探してください。観点:
- 目標の方向性で求められるスキル・技術トレンド
- 該当職種の採用動向・市場価値に関する情報
- 経歴とのギャップを埋める学習リソースや実践知見

{_JSON_FORMAT}
各要素には "relevance"(なぜこの人に関連するか、日本語1〜2文)も追加してください。
ルール:
- 指定された最大件数まで。質を優先し、無理に件数を埋めない
- 既知URLリストに含まれるものは除外
- 該当が無ければ [] を返す
"""


def build_system_prompt(kind: str) -> str:
    match kind:
        case "topic":
            return _TOPIC_SYSTEM
        case "career":
            return _CAREER_SYSTEM
        case _:
            raise ValueError(f"unknown collection kind: {kind}")


def build_user_prompt(req: CollectionRequest) -> str:
    if req.kind == "topic":
        head = f"# トピック\n{req.query_text}"
    else:
        # query_text にはレジュメ+方向性が整形済みで入る(services/collector.py)
        head = req.query_text

    known = (
        "\n".join(f"- {u}" for u in req.known_urls) if req.known_urls else "(なし)"
    )
    return f"""\
{head}

# 最大件数
{req.max_articles}

# 既知URL(除外対象)
{known}
"""
