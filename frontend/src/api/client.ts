// 最小のfetchラッパ。/api はvite devサーバがFastAPI(:8000)へプロキシする
// TODO(ステップ4以降): openapi-typescript で生成した型に置き換える(docs/DESIGN.md §7)
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`)
  }
  return res.json() as Promise<T>
}
