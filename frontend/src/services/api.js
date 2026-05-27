import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.response.use(
  (r) => r.data,
  (err) => Promise.reject(err.response?.data || err.message),
)

export const projects = {
  list: () => api.get('/projects/'),
  create: (data) => api.post('/projects/', data),
  get: (id) => api.get(`/projects/${id}/`),
  update: (id, data) => api.put(`/projects/${id}/`, data),
  delete: (id) => api.delete(`/projects/${id}/`),
}

export const compounds = {
  search: (q) => api.get('/compounds/search/', { params: { q } }),
  create: (data) => api.post('/compounds/', data),
  get: (id) => api.get(`/compounds/${id}/`),
  list: (projectId) => api.get('/compounds/', { params: { project_id: projectId } }),
  properties: (id) => api.get(`/compounds/${id}/properties/`),
  admet: (id) => api.get(`/compounds/${id}/admet/`),
  safety: (id) => api.get(`/compounds/${id}/safety/`),
  targets: (id) => api.get(`/compounds/${id}/targets/`),
  structureUrl: (id) => `/api/compounds/${id}/structure/`,
  similar: (id) => api.get(`/compounds/${id}/similar/`),
  spectra: (cas, type) => api.get('/compounds/spectra/', { params: { cas, type } }),
}

export const diseases = {
  search: (q) => api.get('/diseases/search/', { params: { q } }),
  targets: (efoId) => api.get(`/diseases/${efoId}/targets/`),
  drugs: (efoId) => api.get(`/diseases/${efoId}/drugs/`),
}

export const targets = {
  detail: (uniprotId) => api.get(`/targets/${uniprotId}/`),
}

export const experiments = {
  recent: () => api.get('/experiments/recent/'),
  list: (projectId) => api.get('/experiments/', { params: { project_id: projectId } }),
  create: (data) => api.post('/experiments/', data),
  get: (id) => api.get(`/experiments/${id}/`),
  update: (id, data) => api.put(`/experiments/${id}/`, data),
  results: (id) => api.get(`/experiments/${id}/results/`),
  logResult: (id, data) => api.post(`/experiments/${id}/results/`, data),
}

export const risk = {
  get: (projectId) => api.get(`/projects/${projectId}/risk-assessment/`),
  save: (projectId, data) => api.post(`/projects/${projectId}/risk-assessment/`, data),
}

export const synthesis = {
  retro: (data) => api.post('/synthesis/retro/', data),
  tree: (data) => api.post('/synthesis/tree/', data),
  forward: (data) => api.post('/synthesis/forward/', data),
  conditions: (data) => api.post('/synthesis/conditions/', data),
  buyables: (smiles) => api.get('/synthesis/buyables/', { params: { smiles } }),
}

export const literature = {
  search: (q, max = 20) => api.get('/literature/search/', { params: { q, max } }),
  article: (pmid) => api.get(`/literature/${pmid}/`),
  trials: (params) => api.get('/trials/search/', { params }),
  trial: (nctId) => api.get(`/trials/${nctId}/`),
}

export const regulatory = {
  guidance: (q) => api.get('/regulatory/guidance/', { params: { q } }),
  labels: (drug) => api.get('/regulatory/labels/', { params: { drug } }),
  ndc: (drug) => api.get('/regulatory/ndc/', { params: { drug } }),
  excipients: (form) => api.get('/regulatory/excipients/', { params: { form } }),
}

export const chat = {
  sessions: (projectId) => api.get('/chat/sessions/', { params: projectId ? { project_id: projectId } : {} }),
  session: (id) => api.get(`/chat/sessions/${id}/`),
  createSession: (data) => api.post('/chat/sessions/', data),
  deleteSession: (id) => api.delete(`/chat/sessions/${id}/`),
}

export const documents = {
  list: (projectId) => api.get(`/projects/${projectId}/documents/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/documents/`, data),
  get: (id) => api.get(`/documents/${id}/`),
  update: (id, data) => api.put(`/documents/${id}/`, data),
  exportUrl: (id) => `/api/documents/${id}/export/`,
}

export async function* createSSEStream(url, options = {}) {
  const response = await fetch(url, {
    method: options.method || 'POST',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('data: ')) {
        const jsonStr = trimmed.slice(6)
        if (jsonStr) {
          try {
            yield JSON.parse(jsonStr)
          } catch {
            // skip malformed
          }
        }
      }
    }
  }
}

export default api
