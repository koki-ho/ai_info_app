import { useMutation, useQueryClient } from '@tanstack/react-query'
import { markArticle } from '../api/client'
import type { Article } from '../api/types'

export default function ArticleCard({ article }: { article: Article }) {
  const queryClient = useQueryClient()
  const toggleRead = useMutation({
    mutationFn: () => markArticle(article.id, !article.is_read),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['articles'] }),
  })

  return (
    <article
      className={`rounded-lg border bg-white p-4 shadow-sm ${
        article.is_read ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold leading-snug">
          <a
            href={article.url}
            target="_blank"
            rel="noreferrer"
            className="text-blue-700 hover:underline"
          >
            {article.title}
          </a>
        </h3>
        <button
          onClick={() => toggleRead.mutate()}
          disabled={toggleRead.isPending}
          className="shrink-0 rounded border px-2 py-0.5 text-xs text-gray-500 hover:bg-gray-100"
          title={article.is_read ? '未読に戻す' : '既読にする'}
        >
          {article.is_read ? '既読' : '未読'}
        </button>
      </div>
      <div className="mt-1 flex gap-3 text-xs text-gray-500">
        {article.source && <span>{article.source}</span>}
        {article.published_at && <span>{article.published_at}</span>}
        {article.kind === 'career' && (
          <span className="rounded bg-purple-100 px-1.5 text-purple-700">キャリア</span>
        )}
      </div>
      <p className="mt-2 text-sm text-gray-700">{article.summary}</p>
      {article.relevance && (
        <p className="mt-2 rounded bg-purple-50 p-2 text-sm text-purple-800">
          {article.relevance}
        </p>
      )}
    </article>
  )
}
