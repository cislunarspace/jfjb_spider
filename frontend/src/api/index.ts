export interface CrawlRequest {
  paper_type: 'jfjb' | 'rmrb' | 'gmrb'
  paper_date?: string
  start_date?: string
  end_date?: string
  output_dir: string
  export_individual: boolean
  export_combined: boolean
  font_dir?: string
}

export interface CrawlEvent {
  type: 'progress' | 'log' | 'finished' | 'error'
  current?: number
  total?: number
  message?: string
  level?: 'INFO' | 'WARNING' | 'ERROR' | 'STDERR'
  success?: number
  fail?: number
  skip?: number
}

export interface FileInfo {
  name: string
  path: string
  size: number
  modified: string
  is_dir: boolean
}

export interface CrawlStatus {
  running: boolean
  task_id: string | null
}

const BASE = '/api'

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => ({}))
    const message =
      typeof body === 'object' && body !== null && 'error' in body
        ? String((body as Record<string, unknown>).error)
        : `请求失败: ${res.status}`
    throw new Error(message)
  }
  return res.json()
}

export async function startCrawl(req: CrawlRequest): Promise<{ task_id: string }> {
  return apiFetch('/crawl', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

export async function cancelCrawl(): Promise<void> {
  await apiFetch('/crawl/cancel', { method: 'POST' })
}

export async function getStatus(): Promise<CrawlStatus> {
  return apiFetch('/status')
}

export async function listFiles(subPath?: string): Promise<FileInfo[]> {
  const query = subPath ? `?path=${encodeURIComponent(subPath)}` : ''
  return apiFetch(`/files${query}`)
}

export function getFileUrl(filePath: string): string {
  return `${BASE}/files/${encodeURIComponent(filePath)}`
}

export function createEventSource(): EventSource {
  return new EventSource(`${BASE}/crawl/stream`)
}
