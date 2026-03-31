/**
 * API client: thin wrappers around fetch pointing at /api/*.
 * In production the FastAPI server serves everything on the same origin.
 * In dev mode Vite proxies /api → http://localhost:8765.
 */

const BASE = ''  // same-origin

async function _request(method, path, body, isForm = false) {
  const opts = {
    method,
    headers: {},
  }
  if (body) {
    if (isForm) {
      opts.body = body  // FormData
    } else {
      opts.headers['Content-Type'] = 'application/json'
      opts.body = JSON.stringify(body)
    }
  }
  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try {
      const err = await res.json()
      msg = err.detail || msg
    } catch (_) {}
    throw new Error(msg)
  }
  if (res.status === 204) return null
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.blob()
}

const get    = (path)         => _request('GET',    path)
const post   = (path, body)   => _request('POST',   path, body)
const patch  = (path, body)   => _request('PATCH',  path, body)
const del    = (path)         => _request('DELETE', path)
const upload = (path, form)   => _request('POST',   path, form, true)

// ---- helpers ----
const qs = (params) => {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') s.append(k, v) })
  return s.toString() ? '?' + s.toString() : ''
}

// ---- Projects ----
export const api = {
  // Projects
  getProjects:          ()          => get('/api/projects'),
  createProject:        (data)      => post('/api/projects', data),
  updateProject:        (id, data)  => patch(`/api/projects/${id}`, data),
  deleteProject:        (id)        => del(`/api/projects/${id}`),

  // Locations
  getLocations:         (projectId, tree = false) =>
    get(`/api/locations${qs({ project_id: projectId, tree })}`),
  createLocation:       (data)      => post('/api/locations', data),
  updateLocation:       (id, data)  => patch(`/api/locations/${id}`, data),
  deleteLocation:       (id)        => del(`/api/locations/${id}`),
  locationSubtreeIds:   (id)        => get(`/api/locations/${id}/subtree-ids`),

  // Taxa
  getTaxa:              (projectId, { tree, search, rank, recordable } = {}) =>
    get(`/api/taxa${qs({ project_id: projectId, tree, search, rank, recordable })}`),
  createTaxon:          (data)      => post('/api/taxa', data),
  updateTaxon:          (id, data)  => patch(`/api/taxa/${id}`, data),
  deleteTaxon:          (id)        => del(`/api/taxa/${id}`),
  mergePreview:         (data)      => post('/api/taxa/merge/preview', data),
  mergeExecute:         (data)      => post('/api/taxa/merge/execute', data),
  getMergeLogs:         (projectId) => get(`/api/taxa/merge/logs${qs({ project_id: projectId })}`),

  // Methods
  getMethods:           (projectId) => get(`/api/methods${qs({ project_id: projectId })}`),
  createMethod:         (data)      => post('/api/methods', data),
  updateMethod:         (id, data)  => patch(`/api/methods/${id}`, data),
  deleteMethod:         (id)        => del(`/api/methods/${id}`),

  // Sampling events
  getEvents:            (projectId, locationId) =>
    get(`/api/sampling/events${qs({ project_id: projectId, location_id: locationId })}`),
  createEvent:          (data)      => post('/api/sampling/events', data),
  updateEvent:          (id, data)  => patch(`/api/sampling/events/${id}`, data),
  deleteEvent:          (id)        => del(`/api/sampling/events/${id}`),

  // Replicates
  getReplicates:        (eventId)   => get(`/api/sampling/events/${eventId}/replicates`),
  createReplicate:      (data)      => post('/api/sampling/replicates', data),
  updateReplicate:      (id, data)  => patch(`/api/sampling/replicates/${id}`, data),
  deleteReplicate:      (id)        => del(`/api/sampling/replicates/${id}`),

  // Records
  getRecords:           (projectId, filters = {}) =>
    get(`/api/records${qs({ project_id: projectId, ...filters })}`),
  createRecord:         (data)      => post('/api/records', data),
  updateRecord:         (id, data)  => patch(`/api/records/${id}`, data),
  deleteRecord:         (id)        => del(`/api/records/${id}`),

  // Media
  getMedia:             (projectId, linkedToType, linkedToId) =>
    get(`/api/media${qs({ project_id: projectId, linked_to_type: linkedToType, linked_to_id: linkedToId })}`),
  updateMedia:          (id, data)  => patch(`/api/media/${id}`, data),
  deleteMedia:          (id)        => del(`/api/media/${id}`),
  mediaFileUrl:         (id)        => `/api/media/${id}/file`,
  mediaThumbnailUrl:    (id)        => `/api/media/${id}/thumbnail`,

  // Upload
  getUploadQR:          (projectId) => get(`/api/upload/qr${qs({ project_id: projectId })}`),
  searchDestinations:   (projectId, q) =>
    get(`/api/upload/destinations${qs({ project_id: projectId, q })}`),
  uploadFiles:          (formData)  => upload('/api/upload/files', formData),

  // Analyses
  runShannon:           (body)      => post('/api/analyses/shannon', body),
  runSimpson:           (body)      => post('/api/analyses/simpson', body),
  runAccumulation:      (body)      => post('/api/analyses/accumulation', body),
  runBrayCurtis:        (body)      => post('/api/analyses/bray-curtis', body),
  runJaccard:           (body)      => post('/api/analyses/jaccard', body),
  runRichness:          (body)      => post('/api/analyses/richness', body),

  // Exports
  exportUrl:            (type, projectId, extra = {}) =>
    `/api/exports/${type}${qs({ project_id: projectId, ...extra })}`,
  manualBackup:         (projectId) =>
    _request('POST', `/api/exports/backup${qs({ project_id: projectId })}`),
}

export default api
