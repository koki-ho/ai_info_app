import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, getRun, startCollect } from '../api/client'
import type { CollectScope, Run } from '../api/types'

/**
 * 収集実行+runポーリング(docs/DESIGN.md §6, §8)。
 * POST /api/collect → run_id を 2.5秒間隔でポーリングし、
 * 完了したら articles / runs のクエリを無効化してフィードを再取得させる。
 */
export function useCollectRun() {
  const queryClient = useQueryClient()
  const [runId, setRunId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (scope: CollectScope) => startCollect(scope),
    onSuccess: ({ run_id }) => {
      setError(null)
      setRunId(run_id)
    },
    onError: (e) => {
      setError(
        e instanceof ApiError && e.status === 409
          ? '収集は既に実行中です。完了をお待ちください。'
          : `収集の開始に失敗しました: ${e.message}`,
      )
    },
  })

  const { data: run } = useQuery({
    queryKey: ['runs', runId],
    queryFn: () => getRun(runId!),
    enabled: runId != null,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 2500 : false,
  })

  const finished = run != null && run.status !== 'running'
  useEffect(() => {
    if (finished) {
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    }
  }, [finished, queryClient])

  const collecting =
    mutation.isPending || (runId != null && run?.status !== undefined && !finished) ||
    (runId != null && run === undefined)

  const dismiss = () => {
    setRunId(null)
    setError(null)
  }

  return {
    collect: (scope: CollectScope) => mutation.mutate(scope),
    collecting,
    lastRun: (finished ? run : null) as Run | null,
    error,
    dismiss,
  }
}
