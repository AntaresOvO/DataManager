import request from './request'

export function getForms(params) {
  return request.get('/api/forms', { params })
}

export function getForm(id) {
  return request.get(`/api/forms/${id}`)
}

export function createForm(data) {
  return request.post('/api/forms', data)
}

export function updateForm(id, data) {
  return request.put(`/api/forms/${id}`, data)
}

export function deleteForm(id) {
  return request.delete(`/api/forms/${id}`)
}

export function batchCreateForms(data) {
  return request.post('/api/forms/batch', data)
}
