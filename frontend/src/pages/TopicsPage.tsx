import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createTopic, deleteTopic, listTopics, updateTopic } from '../api/client'
import { useCollectRun } from '../hooks/useCollectRun'

export default function TopicsPage() {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [note, setNote] = useState('')
  const { collect, collecting, lastRun, error } = useCollectRun()

  const { data: topics, isLoading } = useQuery({
    queryKey: ['topics'],
    queryFn: listTopics,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['topics'] })
  const create = useMutation({
    mutationFn: () => createTopic({ name: name.trim(), note: note.trim() || undefined }),
    onSuccess: () => {
      setName('')
      setNote('')
      invalidate()
    },
  })
  const toggle = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      updateTopic(id, { enabled }),
    onSuccess: invalidate,
  })
  const remove = useMutation({
    mutationFn: (id: number) => deleteTopic(id),
    onSuccess: invalidate,
  })

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">トピック管理</h2>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (name.trim()) create.mutate()
        }}
        className="mb-6 space-y-2 rounded-lg border bg-white p-4"
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="トピック名(例: ハーネスエンジニアリング)"
          className="w-full rounded border px-3 py-2 text-sm"
        />
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="検索の補足コンテキスト(任意)"
          className="w-full rounded border px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={!name.trim() || create.isPending}
          className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          追加
        </button>
      </form>

      {error && (
        <p className="mb-3 rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>
      )}
      {lastRun && (
        <p className="mb-3 rounded bg-green-50 p-2 text-sm text-green-700">
          収集が完了しました(ステータス: {lastRun.status})
        </p>
      )}

      {isLoading ? (
        <p className="text-gray-500">読み込み中…</p>
      ) : !topics || topics.length === 0 ? (
        <p className="text-gray-500">トピックが未登録です。上のフォームから追加してください。</p>
      ) : (
        <ul className="space-y-2">
          {topics.map((t) => (
            <li
              key={t.id}
              className="flex items-center gap-3 rounded-lg border bg-white p-3"
            >
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={t.enabled}
                  onChange={(e) =>
                    toggle.mutate({ id: t.id, enabled: e.target.checked })
                  }
                />
              </label>
              <div className="min-w-0 flex-1">
                <p className={`font-medium ${t.enabled ? '' : 'text-gray-400'}`}>
                  {t.name}
                </p>
                {t.note && <p className="truncate text-xs text-gray-500">{t.note}</p>}
              </div>
              <button
                onClick={() => collect({ scope: 'topic', topic_id: t.id })}
                disabled={collecting || !t.enabled}
                className="rounded border px-3 py-1 text-xs hover:bg-gray-100 disabled:opacity-40"
              >
                {collecting ? '収集中…' : '今すぐ収集'}
              </button>
              <button
                onClick={() => {
                  if (confirm(`「${t.name}」を削除しますか?(収集済み記事も削除されます)`)) {
                    remove.mutate(t.id)
                  }
                }}
                className="rounded border border-red-200 px-3 py-1 text-xs text-red-600 hover:bg-red-50"
              >
                削除
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
