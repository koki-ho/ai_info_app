# TODO(ステップ3): 収集オーケストレーション(docs/DESIGN.md §6)
# - 対象(有効トピック / キャリアプロフィール)の列挙
# - 既知URL(直近200件)取得 → llm.factory.get_collector().collect(req)
# - (user_id, url) で upsert、対象単位の失敗はスキップして detail に記録
# - asyncio.Semaphore(2) で並列度制御
