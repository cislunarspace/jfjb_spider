export interface CrawlRequest {
  paper_type: 'jfjb' | 'rmrb'
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
  level?: string
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

export async function startCrawl(req: CrawlRequest): Promise<{ task_id: string }> {
  const res = await fetch(`${BASE}/crawl`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || '启动抓取失败')
  }
  return res.json()
}

export async function cancelCrawl(): Promise<void> {
  const res = await fetch(`${BASE}/crawl/cancel`, { method: 'POST' })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.error || '取消失败')
  }
}

export async function getStatus(): Promise<CrawlStatus> {
  const res = await fetch(`${BASE}/status`)
  return res.json()
}

export async function listFiles(subPath?: string): Promise<FileInfo[]> {
  const url = subPath
    ? `${BASE}/files?path=${encodeURIComponent(subPath)}`
    : `${BASE}/files`
  const res = await fetch(url)
  return res.json()
}

export function getFileUrl(filePath: string): string {
  return `${BASE}/files/${encodeURIComponent(filePath)}`
}

export function createEventSource(): EventSource {
  return new EventSource(`${BASE}/crawl/stream`)
}
