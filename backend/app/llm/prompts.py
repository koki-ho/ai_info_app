# TODO(ステップ2): プロバイダ非依存のプロンプト(docs/DESIGN.md §4.3)
# - build_system_prompt(kind): トピック収集 / キャリア収集のシステム指示 + 出力JSONフォーマット
# - build_user_prompt(req): query_text と known_urls の注入


def build_system_prompt(kind: str) -> str:
    raise NotImplementedError


def build_user_prompt(req) -> str:
    raise NotImplementedError
