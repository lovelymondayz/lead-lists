import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// ── Stats ──
export async function getStats() {
  const res = await api.get('/stats')
  return res.data
}

// ── Jobs ──
export async function getJobs() {
  const res = await api.get('/jobs')
  return res.data
}

export async function getJob(id: number) {
  const res = await api.get(`/jobs/${id}`)
  return res.data
}

// ── Sources ──
export async function getSources() {
  const res = await api.get('/sources')
  return res.data
}

// ── Scrape ──
export async function scrape(url: string, keywords?: string) {
  const res = await api.post('/scrape', { url, keywords })
  return res.data
}