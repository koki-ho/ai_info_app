import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getCareer, putCareer } from '../api/client'
import type { CareerProfile } from '../api/types'

export default function CareerPage() {
  const { data: profile, isLoading } = useQuery({
    queryKey: ['career'],
    queryFn: getCareer,
  })

  if (isLoading) {
    return <p className="text-gray-500">読み込み中…</p>
  }

  return (
    <section>
      <h2 className="mb-1 text-xl font-semibold">キャリア設定</h2>
      <p className="mb-4 text-sm text-gray-500">
        履歴書(職務経歴)とキャリアの方向性を登録すると、収集時にその文脈に合わせた
        キャリアアップ関連の記事・ニュースも収集されます。
      </p>
      {/* keyで再マウントし、サーバ状態をフォーム初期値に反映する */}
      <CareerForm key={profile?.updated_at ?? 'new'} initial={profile ?? null} />
    </section>
  )
}

function CareerForm({ initial }: { initial: CareerProfile | null }) {
  const queryClient = useQueryClient()
  const [resumeText, setResumeText] = useState(initial?.resume_text ?? '')
  const [direction, setDirection] = useState(initial?.career_direction ?? '')
  const [enabled, setEnabled] = useState(initial?.enabled ?? true)
  const [saved, setSaved] = useState(false)

  const save = useMutation({
    mutationFn: () =>
      putCareer({
        resume_text: resumeText,
        career_direction: direction,
        enabled,
      }),
    onSuccess: () => {
      setSaved(true)
      queryClient.invalidateQueries({ queryKey: ['career'] })
    },
  })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        setSaved(false)
        save.mutate()
      }}
      className="space-y-4 rounded-lg border bg-white p-4"
    >
      <div>
        <label className="mb-1 block text-sm font-medium">履歴書・職務経歴</label>
        <textarea
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          rows={10}
          placeholder="経歴・スキル・実績などをテキストで貼り付けてください"
          className="w-full rounded border px-3 py-2 text-sm"
        />
      </div>
      <div>
        <label className="mb-1 block text-sm font-medium">キャリアの方向性</label>
        <textarea
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
          rows={3}
          placeholder="例: MLエンジニアからAIプラットフォームのテックリードへ"
          className="w-full rounded border px-3 py-2 text-sm"
        />
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
        />
        キャリア収集を有効にする(「すべて」更新時に含める)
      </label>
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={!resumeText.trim() || !direction.trim() || save.isPending}
          className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {save.isPending ? '保存中…' : '保存'}
        </button>
        {saved && <span className="text-sm text-green-700">保存しました</span>}
        {save.isError && (
          <span className="text-sm text-red-700">保存に失敗しました</span>
        )}
      </div>
    </form>
  )
}
