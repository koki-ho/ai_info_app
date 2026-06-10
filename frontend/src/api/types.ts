// バックエンド app/schemas.py に対応する型
// TODO: openapi-typescript での自動生成に置き換え可能(docs/DESIGN.md §7)

export interface Topic {
  id: number
  name: string
  note: string | null
  enabled: boolean
  created_at: string
}

export interface CareerProfile {
  id: number
  resume_text: string
  career_direction: string
  enabled: boolean
  updated_at: string
}

export interface Article {
  id: number
  topic_id: number | null
  kind: 'topic' | 'career'
  title: string
  url: string
  source: string | null
  published_at: string | null
  summary: string
  relevance: string | null
  is_read: boolean
  collected_at: string
}

export interface Run {
  id: number
  scope: string
  status: 'running' | 'success' | 'partial' | 'failed'
  detail: string | null
  started_at: string
  finished_at: string | null
}

export type CollectScope =
  | { scope: 'all' }
  | { scope: 'career' }
  | { scope: 'topic'; topic_id: number }
