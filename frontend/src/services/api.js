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
  delete: (id) => api.delete(`/compounds/${id}/`),
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

export const experiments = {
  recent: () => api.get('/experiments/recent/'),
  list: (projectId, params = {}) => api.get('/experiments/', { params: { project_id: projectId, ...params } }),
  listByPlan: (planId) => api.get('/experiments/', { params: { synthesis_plan: planId } }),
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

export const drugs = {
  search: (q) => api.get('/drugs/search/', { params: { q } }),
  get: (chemblId) => api.get(`/drugs/${chemblId}/`),
  synthesis: (chemblId) => api.get(`/drugs/${chemblId}/synthesis/`),
  trials: (chemblId) => api.get(`/drugs/${chemblId}/trials/`),
  patents: (chemblId) => api.get(`/drugs/${chemblId}/patents/`),
}

export const patents = {
  search: (q, smiles) => api.get('/patents/', { params: { q, smiles } }),
  get: (patentNumber) => api.get(`/patents/${encodeURIComponent(patentNumber)}/`),
}

export const analogs = {
  search: (smiles, threshold) => api.post('/analogs/search/', { smiles, threshold }),
  patentCheck: (candidates) => api.post('/analogs/patent-check/', { candidates }),
  admet: (smiles_list) => api.post('/analogs/admet/', { smiles_list }),
  update: (id, data) => api.patch(`/analog-candidates/${id}/`, data),
}

export const investigations = {
  list: () => api.get('/investigations/'),
  create: (data) => api.post('/investigations/', data),
  get: (id) => api.get(`/investigations/${id}/`),
  update: (id, data) => api.put(`/investigations/${id}/`, data),
  candidates: (id) => api.get(`/investigations/${id}/candidates/`),
  addCandidate: (id, data) => api.post(`/investigations/${id}/candidates/`, data),
  linkProject: (id, projectId, linkShortlisted = true) =>
    api.post(`/investigations/${id}/link-project/`, { project: projectId, link_shortlisted: linkShortlisted }),
}

export const synthesisPlan = {
  list: (params) => api.get('/synthesis-plans/', { params: typeof params === 'object' ? params : { project: params } }),
  create: (data) => api.post('/synthesis-plans/', data),
  get: (id) => api.get(`/synthesis-plans/${id}/`),
  update: (id, data) => api.patch(`/synthesis-plans/${id}/`, data),
  delete: (id) => api.delete(`/synthesis-plans/${id}/`),
  planExperiments: (id) => api.post(`/synthesis-plans/${id}/plan-experiments/`),
}

export const analogCandidates = {
  update: (id, data) => api.patch(`/analog-candidates/${id}/`, data),
}

// ─── v2 API modules ──────────────────────────────────────────────────────────

export const projectPhases = {
  list: (projectId) => api.get(`/projects/${projectId}/phases/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/phases/`, data),
  get: (projectId, phaseId) => api.get(`/projects/${projectId}/phases/${phaseId}/`),
  update: (projectId, phaseId, data) => api.patch(`/projects/${projectId}/phases/${phaseId}/`, data),
  decision: (projectId, phaseId, data) => api.post(`/projects/${projectId}/phases/${phaseId}/decision/`, data),
}

export const targets = {
  // v1 compatibility
  detail: (uniprotId) => api.get(`/targets/${uniprotId}/`),
  // v2 target profiles
  listProfiles: () => api.get('/target-profiles/'),
  createProfile: (data) => api.post('/target-profiles/', data),
  getProfile: (id) => api.get(`/target-profiles/${id}/`),
  updateProfile: (id, data) => api.patch(`/target-profiles/${id}/`, data),
  pdb: (id) => api.get(`/target-profiles/${id}/pdb/`),
  bindingSites: (id, pdbId) => api.get(`/target-profiles/${id}/binding-sites/`, { params: pdbId ? { pdb_id: pdbId } : {} }),
  saveBindingSite: (id, data) => api.post(`/target-profiles/${id}/binding-sites/`, data),
  uniprot: (id) => api.get(`/target-profiles/${id}/uniprot/`),
}

export const virtualScreening = {
  createRun: (data) => api.post('/virtual-screening/runs/', data),
  getRun: (id) => api.get(`/virtual-screening/runs/${id}/`),
  poll: (id) => api.get(`/virtual-screening/runs/${id}/poll/`),
  hits: (runId, shortlisted = false) => api.get(`/virtual-screening/runs/${runId}/hits/`, { params: shortlisted ? { shortlisted: 'true' } : {} }),
  shortlistHit: (hitId, data) => api.patch(`/virtual-screening/hits/${hitId}/shortlist/`, data),
}

export const sar = {
  list: (projectId) => api.get(`/projects/${projectId}/sar/`),
  create: (data) => api.post(`/projects/${data.project}/sar/`, data),
  get: (id) => api.get(`/sar-entries/${id}/`),
  update: (id, data) => api.patch(`/sar-entries/${id}/`, data),
  delete: (id) => api.delete(`/sar-entries/${id}/`),
  heatmap: (projectId) => api.get(`/projects/${projectId}/sar/heatmap/`),
}

export const formulation = {
  getByProject: (projectId) => api.get(`/projects/${projectId}/formulation/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/formulation/`, data),
  get: (id) => api.get(`/formulation-plans/${id}/`),
  update: (id, data) => api.patch(`/formulation-plans/${id}/`, data),
  addComponent: (planId, data) => api.post(`/formulation-plans/${planId}/components/`, data),
  removeComponent: (planId, componentId) => api.delete(`/formulation-plans/${planId}/components/${componentId}/`),
  checkCompatibility: (planId) => api.post(`/formulation-plans/${planId}/compatibility/`),
  context: (planId) => api.get(`/formulation-plans/${planId}/context/`),
}

export const excipients = {
  search: (params) => api.get('/excipients/search/', { params }),
}

export const saltScreening = {
  list: (projectId) => api.get(`/projects/${projectId}/salt-screens/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/salt-screens/`, data),
  get: (id) => api.get(`/salt-screens/${id}/`),
  update: (id, data) => api.patch(`/salt-screens/${id}/`, data),
  delete: (id) => api.delete(`/salt-screens/${id}/`),
  candidates: (screenId) => api.get(`/salt-screens/${screenId}/candidates/`),
  addCandidate: (screenId, data) => api.post(`/salt-screens/${screenId}/candidates/`, data),
  updateCandidate: (id, data) => api.patch(`/salt-screen-candidates/${id}/`, data),
  deleteCandidate: (id) => api.delete(`/salt-screen-candidates/${id}/`),
  experiments: (screenId) => api.get(`/salt-screens/${screenId}/experiments/`),
  addExperiment: (screenId, data) => api.post(`/salt-screens/${screenId}/experiments/`, data),
  updateExperiment: (id, data) => api.patch(`/salt-screen-experiments/${id}/`, data),
  deleteExperiment: (id) => api.delete(`/salt-screen-experiments/${id}/`),
  ccdc: (params) => api.get('/ccdc/lookup/', { params }),
}

export const stability = {
  getByProject: (projectId) => api.get(`/projects/${projectId}/stability/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/stability/`, data),
  get: (id) => api.get(`/stability-plans/${id}/`),
  update: (id, data) => api.patch(`/stability-plans/${id}/`, data),
  addCondition: (planId, data) => api.post(`/stability-plans/${planId}/conditions/`, data),
  results: (planId, params) => api.get(`/stability-plans/${planId}/results/`, { params }),
  logResult: (planId, data) => api.post(`/stability-plans/${planId}/results/`, data),
  matrix: (planId) => api.get(`/stability-plans/${planId}/matrix/`),
  context: (planId) => api.get(`/stability-plans/${planId}/context/`),
}

export const analytical = {
  list: (projectId) => api.get(`/projects/${projectId}/analytical-methods/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/analytical-methods/`, data),
  get: (id) => api.get(`/analytical-methods/${id}/`),
  update: (id, data) => api.patch(`/analytical-methods/${id}/`, data),
  delete: (id) => api.delete(`/analytical-methods/${id}/`),
  validation: (id) => api.get(`/analytical-methods/${id}/validation/`),
}

export const specifications = {
  list: (projectId) => api.get(`/projects/${projectId}/specifications/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/specifications/`, data),
  get: (id) => api.get(`/specifications/${id}/`),
  update: (id, data) => api.patch(`/specifications/${id}/`, data),
  delete: (id) => api.delete(`/specifications/${id}/`),
}

export const preclinical = {
  list: (projectId) => api.get(`/projects/${projectId}/preclinical/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/preclinical/`, data),
  get: (id) => api.get(`/preclinical-studies/${id}/`),
  update: (id, data) => api.patch(`/preclinical-studies/${id}/`, data),
  delete: (id) => api.delete(`/preclinical-studies/${id}/`),
  logResults: (id, data) => api.patch(`/preclinical-studies/${id}/results/`, data),
  admetDashboard: (projectId) => api.get(`/projects/${projectId}/admet-dashboard/`),
  context: (id) => api.get(`/preclinical-studies/${id}/context/`),
}

export const context = {
  project: (id) => api.get(`/projects/${id}/context/`),
  compound: (id) => api.get(`/compounds/${id}/context/`),
  synthesisPlan: (id) => api.get(`/synthesis-plans/${id}/context/`),
  formulationPlan: (id) => api.get(`/formulation-plans/${id}/context/`),
  stabilityPlan: (id) => api.get(`/stability-plans/${id}/context/`),
  preclinicalStudy: (id) => api.get(`/preclinical-studies/${id}/context/`),
}

// ─── v3 API modules ──────────────────────────────────────────────────────────

export const aiPlan = {
  get: (projectId) => api.get(`/projects/${projectId}/ai-plan/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/ai-plan/`, data),
  update: (planId, data) => api.patch(`/ai-plans/${planId}/`, data),
  getById: (planId) => api.get(`/ai-plans/${planId}/`),
  compressContext: (planId) => api.post(`/ai-plans/${planId}/compress-context/`),
  // Steps
  getStep: (stepId) => api.get(`/ai-plan-steps/${stepId}/`),
  updateStep: (stepId, data) => api.patch(`/ai-plan-steps/${stepId}/`, data),
  approveStep: (stepId) => api.post(`/ai-plan-steps/${stepId}/approve/`),
  rejectStep: (stepId, feedback) => api.post(`/ai-plan-steps/${stepId}/reject/`, { feedback }),
  skipStep: (stepId) => api.post(`/ai-plan-steps/${stepId}/skip/`),
  goBack: (stepId, targetStepNumber) => api.post(`/ai-plan-steps/${stepId}/go-back/`, { target_step_number: targetStepNumber }),
  getDiscussions: (stepId) => api.get(`/ai-plan-steps/${stepId}/discussions/`),
  executeAction: (stepId, actionId, actionType, data) =>
    api.post(`/ai-plan-steps/${stepId}/execute-action/`, { action_id: actionId, action_type: actionType, data }),
}

export const aiLab = {
  sessions: () => api.get('/ai-lab/sessions/'),
  createSession: (data) => api.post('/ai-lab/sessions/', data),
  getSession: (id) => api.get(`/ai-lab/sessions/${id}/`),
  createProject: (id, data) => api.post(`/ai-lab/sessions/${id}/create-project/`, data),
}

export const ragDocuments = {
  list: (params) => api.get('/documents/', { params }),
  get: (id) => api.get(`/documents/${id}/`),
  delete: (id) => api.delete(`/documents/${id}/`),
  search: (params) => api.get('/documents/search/', { params }),
  ingest: (id) => api.post(`/documents/${id}/ingest/`),
}

export const biologics = {
  cellLine: {
    list: (projectId) => api.get(`/projects/${projectId}/cell-line/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/cell-line/`, data),
    get: (id) => api.get(`/cell-line/${id}/`),
    update: (id, data) => api.patch(`/cell-line/${id}/`, data),
    delete: (id) => api.delete(`/cell-line/${id}/`),
  },
  bioprocessing: {
    list: (projectId) => api.get(`/projects/${projectId}/bioprocessing/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/bioprocessing/`, data),
    get: (id) => api.get(`/bioprocessing/${id}/`),
    update: (id, data) => api.patch(`/bioprocessing/${id}/`, data),
    delete: (id) => api.delete(`/bioprocessing/${id}/`),
  },
  purification: {
    list: (projectId) => api.get(`/projects/${projectId}/purification/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/purification/`, data),
    get: (id) => api.get(`/purification/${id}/`),
    update: (id, data) => api.patch(`/purification/${id}/`, data),
    delete: (id) => api.delete(`/purification/${id}/`),
  },
  formulation: {
    list: (projectId) => api.get(`/projects/${projectId}/biologic-formulation/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/biologic-formulation/`, data),
    get: (id) => api.get(`/biologic-formulation/${id}/`),
    update: (id, data) => api.patch(`/biologic-formulation/${id}/`, data),
    delete: (id) => api.delete(`/biologic-formulation/${id}/`),
  },
  analytics: {
    list: (projectId) => api.get(`/projects/${projectId}/biologic-analytics/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/biologic-analytics/`, data),
    get: (id) => api.get(`/biologic-analytics/${id}/`),
    update: (id, data) => api.patch(`/biologic-analytics/${id}/`, data),
    delete: (id) => api.delete(`/biologic-analytics/${id}/`),
  },
}

// Unified namespace for stores — avoids importing every named export individually
export const apiClient = {
  projects, compounds, diseases, targets, experiments, risk, synthesis,
  literature, regulatory, chat, documents, drugs, patents, analogs,
  investigations, synthesisPlan, analogCandidates,
  // v2
  projectPhases, virtualScreening, sar, formulation, excipients,
  saltScreening, stability, analytical, specifications, preclinical, context,
  // v3
  aiPlan, aiLab, ragDocuments, biologics,
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
