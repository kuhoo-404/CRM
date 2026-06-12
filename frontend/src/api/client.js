import axios from 'axios'

const api = axios.create({ baseURL: '' })

export const fetchStats = () => api.get('/dashboard/stats').then(r => r.data.data)
export const fetchCategoryBreakdown = (days = 0) => api.get(`/dashboard/category-breakdown?days=${days}`).then(r => r.data.data)
export const fetchThreads = () => api.get('/threads').then(r => r.data.data)
export const fetchThread = (email) => api.get(`/threads/${email}`).then(r => r.data.data)
export const fetchContact = (email) => api.get(`/contacts/${email}`).then(r => r.data.data)
export const fetchSentimentTrend = (sender, days = 0) => api.get(`/rag/analytics/sentiment-trend?sender=${sender}&days=${days}`).then(r => r.data.data)
export const fetchAudit = (type, id) => api.get(`/audit/${type}/${id}`).then(r => r.data.data)
export const classifyEmail = (id) => api.post(`/rag/classify/${id}`).then(r => r.data)
export const runAgent = (id) => api.post(`/agent/run/${id}`).then(r => r.data)
export const runAgentDryRun = (id) => api.post(`/agent/dry-run/${id}`).then(r => r.data)
export const approveDraft = (id) => api.post(`/drafts/${id}/approve`).then(r => r.data)
export const updateContactStatus = (email, status) => api.patch(`/contacts/${email}/status`, { status }).then(r => r.data)
export const sendReply = (emailId, replyText) => api.post(`/respond/${emailId}`, { reply_text: replyText }).then(r => r.data)