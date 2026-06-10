import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listArticles, listRuns, listTopics } from '../api/client'
import type { Article, CollectScope } from '../api/types'
import ArticleCard from '../components/ArticleCard'
import { useCollectRun } from '../hooks/useCollectRun'

type Tab = { key: string; label: string; scope: CollectScope }

const STATUS_LABEL: Record<string, string> = {
  success: '収集が完了しました',
  partial: '収集が完了しました(一部失敗)',
  failed: '収集に失敗しました',
}

function groupByDate(articles: Article[]): [string, Article[]][] {
  const groups = new Map<string, Article[]>()
  for (const a of articles) {
    const key = a.published_at ?? '日付不明'
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)!.push(a)
  }
  return [...groups.entries()]
}

export default function FeedPage() {
  const [tabKey, setTabKey] = useState('all')
  const [unreadOnly, setUnreadOnly] = useState(false)
  const { collect, collecting, lastRun, error, dismiss } = useCollectRun()

  const { data: topics } = useQuery({ queryKey: ['topics'], queryFn: listTopics })
  const { data: runs } = useQuery({ queryKey: ['runs'], queryFn: () => listRuns(1) })

  const tabs: Tab[] = [
    { key: 'all', label: 'すべて', scope: { scope: 'all' } },
    { key: 'career', label: 'キャリア', scope: { scope: 'career' } },
    ...(topics ?? [])
      .filter((t) => t.enabled)
      .map((t) => ({
        key: `topic:${t.id}`,
        label: t.name,
        scope: { scope: 'topic', topic_id: t.id } as CollectScope,
      })),
  ]
  const tab = tabs.find((t) => t.key === tabKey) ?? tabs[0]

  const { data: articles, isLoading } = useQuery({
    queryKey: ['articles', tab.key, unreadOnly],
    queryFn: () =>
      listArticles({
        kind: tab.key === 'career' ? 'career' : undefined,
        topic_id: tab.scope.scope === 'topic' ? tab.scope.topic_id : undefined,
        unread_only: unreadOnly,
      }),
  })

  const lastFinished = runs?.[0]?.finished_at

  return (
    <section>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap gap-1 rounded-lg bg-gray-200 p-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTabKey(t.key)}
              className={`rounded-md px-3 py-1 text-sm ${
                t.key === tab.key
                  ? 'bg-white font-semibold shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-3">
          <label className="flex items-center gap-1 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={unreadOnly}
              onChange={(e) => setUnreadOnly(e.target.checked)}
            />
            未読のみ
          </label>
          <button
            onClick={() => {
              dismiss()
              collect(tab.scope)
            }}
            disabled={collecting}
            className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {collecting ? '収集中…' : `更新(${tab.label})`}
          </button>
        </div>
      </div>

      {lastFinished && (
        <p className="mb-3 text-xs text-gray-500">
          最終更新: {new Date(lastFinished).toLocaleString('ja-JP')}
        </p>
      )}
      {error && (
        <p className="mb-3 rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>
      )}
      {lastRun && (
        <p
          className={`mb-3 rounded p-2 text-sm ${
            lastRun.status === 'failed'
              ? 'bg-red-50 text-red-700'
              : 'bg-green-50 text-green-700'
          }`}
        >
          {STATUS_LABEL[lastRun.status] ?? lastRun.status}
        </p>
      )}

      {isLoading ? (
        <p className="text-gray-500">読み込み中…</p>
      ) : !articles || articles.length === 0 ? (
        <p className="text-gray-500">
          記事がありません。「更新」ボタンで収集を実行してください。
        </p>
      ) : (
        <div className="space-y-6">
          {groupByDate(articles).map(([date, items]) => (
            <div key={date}>
              <h2 className="mb-2 text-sm font-semibold text-gray-500">{date}</h2>
              <div className="space-y-3">
                {items.map((a) => (
                  <ArticleCard key={a.id} article={a} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
