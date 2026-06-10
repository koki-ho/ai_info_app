import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

// TODO(ステップ5): タブ(すべて/キャリア/トピック別)、記事カード、更新ボタン+runポーリング(docs/DESIGN.md §8)
export default function FeedPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api<{ status: string; llm_provider: string }>('/api/health'),
  })

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">フィード</h2>
      <p className="text-gray-500">
        {isLoading
          ? 'バックエンド確認中…'
          : data
            ? `バックエンド接続OK(LLM: ${data.llm_provider})`
            : 'バックエンドに接続できません'}
      </p>
    </section>
  )
}
