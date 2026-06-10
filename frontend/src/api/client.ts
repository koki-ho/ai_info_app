import type {
  Article,
  CareerProfile,
  CollectScope,
  Run,
  Topic,
} from './types'

// 最小のfetchラッパ。/api はvite devサーバがFastAPI(:8000)へプロキシする
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    throw new ApiError(res.status, `API error ${res.status}: ${await res.text()}`)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

// --- topics
export const listTopics = () => api<Topic[]>('/api/topics')
export const createTopic = (body: { name: string; note?: string }) =>
  api<Topic>('/api/topics', { method: 'POST', body: JSON.stringify(body) })
export const updateTopic = (
  id: number,
  body: Partial<Pick<Topic, 'name' | 'note' | 'enabled'>>,
) => api<Topic>(`/api/topics/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
export const deleteTopic = (id: number) =>
  api<void>(`/api/topics/${id}`, { method: 'DELETE' })

// --- career(未登録時は404 → nullを返す)
export const getCareer = () =>
  api<CareerProfile>('/api/career').catch((e) => {
    if (e instanceof ApiError && e.status === 404) return null
    throw e
  })
export const putCareer = (body: {
  resume_text: string
  career_direction: string
  enabled: boolean
}) => api<CareerProfile>('/api/career', { method: 'PUT', body: JSON.stringify(body) })

// --- articles
export const listArticles = (params: {
  kind?: 'topic' | 'career'
  topic_id?: number
  unread_only?: boolean
  page?: number
}) => {
  const qs = new URLSearchParams()
  if (params.kind) qs.set('kind', params.kind)
  if (params.topic_id != null) qs.set('topic_id', String(params.topic_id))
  if (params.unread_only) qs.set('unread_only', 'true')
  if (params.page) qs.set('page', String(params.page))
  return api<Article[]>(`/api/articles?${qs}`)
}
export const markArticle = (id: number, is_read: boolean) =>
  api<Article>(`/api/articles/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ is_read }),
  })

// --- collect / runs
export const startCollect = (body: CollectScope) =>
  api<{ run_id: number }>('/api/collect', { method: 'POST', body: JSON.stringify(body) })
export const getRun = (id: number) => api<Run>(`/api/runs/${id}`)
export const listRuns = (limit = 5) => api<Run[]>(`/api/runs?limit=${limit}`)
