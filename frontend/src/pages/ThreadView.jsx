import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchThread, fetchContact, runAgent, runAgentDryRun, approveDraft, fetchAudit } from '../api/client'
import { UrgencyBadge, CategoryBadge, SentimentBadge, StatusBadge } from '../components/Badge'
import { ArrowLeft, ChevronDown, ChevronRight, Bot, Database, User, AlertTriangle, CheckCircle, Zap } from 'lucide-react'

export default function ThreadView() {
  const { email } = useParams()
  const navigate = useNavigate()
  const decodedEmail = decodeURIComponent(email)

  const [thread, setThread] = useState(null)
  const [contact, setContact] = useState(null)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [agentResult, setAgentResult] = useState(null)
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [agentLoading, setAgentLoading] = useState(false)
  const [reasoningOpen, setReasoningOpen] = useState(true)
  const [ragOpen, setRagOpen] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [t, c] = await Promise.all([
          fetchThread(decodedEmail),
          fetchContact(decodedEmail).catch(() => null),
        ])
        const threadData = Array.isArray(t) ? t[0] : t
        setThread(threadData)
        if (threadData?.emails?.length > 0) {
          const latest = threadData.emails[threadData.emails.length - 1]
          setSelectedEmail(latest)
          // Load audit for latest email
          if (latest?.id) {
            fetchAudit('email', latest.id).then(a => setAuditLogs(a?.logs || [])).catch(() => {})
          }
        }
        setContact(c)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [decodedEmail])

  const handleRunAgent = async (dryRun = true) => {
    if (!selectedEmail) return
    setAgentLoading(true)
    try {
      const result = dryRun
        ? await runAgentDryRun(selectedEmail.id)
        : await runAgent(selectedEmail.id)
      setAgentResult(result.data)
    } catch (e) {
      console.error(e)
    } finally {
      setAgentLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!agentResult?.reasoning_trace) return
    // Find action ID from audit logs
    const actionLog = auditLogs.find(l => l.action === 'classified')
    if (actionLog) {
      await approveDraft(actionLog.entity_id)
      window.location.reload()
    }
  }

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">
      Loading thread...
    </div>
  )

  if (!thread) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">
      Thread not found
    </div>
  )

  const emails = thread.emails || []

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 px-6 py-3 flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-1.5 rounded-lg hover:bg-slate-800 transition-colors">
          <ArrowLeft size={16} className="text-slate-400" />
        </button>
        <div className="flex-1">
          <h2 className="text-sm font-semibold text-white">{thread.subject}</h2>
          <p className="text-xs text-slate-500">{decodedEmail} · {emails.length} emails</p>
        </div>
        <StatusBadge status={thread.status} />
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* LEFT — Email timeline */}
        <div className="w-80 border-r border-slate-800 bg-slate-900/30 flex flex-col overflow-y-auto">
          <div className="p-3 border-b border-slate-800">
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wider">Thread Timeline</p>
          </div>
          <div className="flex-1 p-3 space-y-2">
            {emails.map((e, i) => (
              <div
                key={e.id}
                onClick={() => setSelectedEmail(e)}
                className={`p-3 rounded-lg cursor-pointer border transition-all ${
                  selectedEmail?.id === e.id
                    ? 'bg-blue-600/20 border-blue-500/50'
                    : 'bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-slate-400">#{i + 1} — {e.message_id}</span>
                  <SentimentBadge score={e.sentiment_score} />
                </div>
                <p className="text-xs font-medium text-slate-200 truncate">{e.subject}</p>
                <p className="text-xs text-slate-500 mt-1 truncate">{(e.body || '').slice(0, 60)}...</p>
                <div className="flex gap-1 mt-2 flex-wrap">
                  <CategoryBadge category={e.category} />
                  <UrgencyBadge urgency={e.urgency} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CENTER — Email content */}
        <div className="flex-1 flex flex-col overflow-y-auto">
          {selectedEmail ? (
            <div className="p-6 space-y-4">
              {/* Email header */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-white">{selectedEmail.subject}</h3>
                    <p className="text-sm text-slate-400 mt-1">From: {selectedEmail.sender}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {selectedEmail.timestamp ? new Date(selectedEmail.timestamp).toLocaleString() : 'Unknown time'}
                    </p>
                  </div>
                  <div className="flex gap-2 flex-wrap justify-end">
                    <UrgencyBadge urgency={selectedEmail.urgency} />
                    <CategoryBadge category={selectedEmail.category} />
                    <StatusBadge status={selectedEmail.status} />
                  </div>
                </div>

                {/* Classification info */}
                {selectedEmail.confidence && (
                  <div className="bg-slate-800/50 rounded-lg p-3 mb-4 flex gap-4 text-xs">
                    <span className="text-slate-400">Confidence: <span className="text-white font-mono">{(selectedEmail.confidence * 100).toFixed(0)}%</span></span>
                    <span className="text-slate-400">Sentiment: <SentimentBadge score={selectedEmail.sentiment_score} /></span>
                    {selectedEmail.requires_human && (
                      <span className="text-orange-400 flex items-center gap-1">
                        <AlertTriangle size={12} /> Requires Human
                      </span>
                    )}
                  </div>
                )}

                {/* Email body */}
                <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap border-t border-slate-800 pt-4">
                  {selectedEmail.body || 'No body content'}
                </div>

                {/* Entities */}
                {selectedEmail.raw_entities && Object.values(selectedEmail.raw_entities).some(v => v?.length > 0) && (
                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <p className="text-xs text-slate-500 mb-2 font-medium">Detected Entities</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(selectedEmail.raw_entities).map(([key, vals]) =>
                        (vals || []).map(v => (
                          <span key={`${key}-${v}`} className="text-xs bg-blue-900/30 text-blue-300 border border-blue-700/30 px-2 py-0.5 rounded">
                            {key.replace(/_/g, ' ')}: {v}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Suggested reply */}
              {selectedEmail.suggested_reply && (
                <div className="bg-green-900/20 border border-green-700/30 rounded-xl p-4">
                  <p className="text-xs text-green-400 font-medium mb-2 flex items-center gap-1">
                    <CheckCircle size={12} /> Suggested Auto-Reply
                  </p>
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">{selectedEmail.suggested_reply}</p>
                </div>
              )}

              {/* Escalation reason */}
              {selectedEmail.escalation_reason && (
                <div className="bg-red-900/20 border border-red-700/30 rounded-xl p-4">
                  <p className="text-xs text-red-400 font-medium mb-1 flex items-center gap-1">
                    <AlertTriangle size={12} /> Escalation Reason
                  </p>
                  <p className="text-sm text-slate-300">{selectedEmail.escalation_reason}</p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => handleRunAgent(true)}
                  disabled={agentLoading}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Bot size={14} className="text-blue-400" />
                  {agentLoading ? 'Running...' : 'Agent Dry Run'}
                </button>
                <button
                  onClick={() => handleRunAgent(false)}
                  disabled={agentLoading}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Zap size={14} />
                  {agentLoading ? 'Running...' : 'Run Agent'}
                </button>
              </div>

              {/* Agent Reasoning Panel */}
              {agentResult && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                  <button
                    onClick={() => setReasoningOpen(!reasoningOpen)}
                    className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-800/50 transition-colors"
                  >
                    <span className="text-sm font-medium flex items-center gap-2">
                      <Bot size={14} className="text-blue-400" />
                      Agent Reasoning Trace
                      <span className="text-xs text-slate-500">
                        ({agentResult.steps_used} steps · {agentResult.action_taken})
                      </span>
                    </span>
                    {reasoningOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </button>
                  {reasoningOpen && (
                    <div className="px-5 pb-5 space-y-3 border-t border-slate-800">
                      {/* Summary */}
                      {agentResult.final_answer && (
                        <div className="mt-3 p-3 bg-blue-900/20 border border-blue-700/30 rounded-lg">
                          <p className="text-xs text-blue-400 font-medium mb-1">Final Answer</p>
                          <p className="text-sm text-slate-300">{agentResult.final_answer}</p>
                        </div>
                      )}
                      {/* RAG chunks */}
                      {agentResult.rag_chunks_used?.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-slate-500 mb-2 font-medium">RAG Context Used</p>
                          <div className="space-y-1">
                            {agentResult.rag_chunks_used.map((c, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs">
                                <Database size={10} className="text-slate-500" />
                                <span className="text-slate-400">{c.source}</span>
                                <div className="flex-1 bg-slate-800 rounded-full h-1.5">
                                  <div
                                    className="bg-blue-500 h-1.5 rounded-full"
                                    style={{ width: `${(c.score * 100).toFixed(0)}%` }}
                                  />
                                </div>
                                <span className="text-slate-500 font-mono">{c.score.toFixed(3)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {/* Steps */}
                      <div className="space-y-3 mt-2">
                        {(agentResult.reasoning_trace || []).map((step, i) => (
                          <div key={i} className="border border-slate-700/50 rounded-lg overflow-hidden">
                            <div className="bg-slate-800/60 px-3 py-2 flex items-center gap-2">
                              <span className="text-xs text-slate-500">Step {step.step}</span>
                              {step.action && (
                                <span className="text-xs bg-blue-900/40 text-blue-300 px-2 py-0.5 rounded font-mono">
                                  {step.action}
                                </span>
                              )}
                            </div>
                            <div className="p-3 space-y-2">
                              {step.thought && (
                                <div>
                                  <p className="text-xs text-yellow-500 font-medium mb-0.5">Thought</p>
                                  <p className="text-xs text-slate-300">{step.thought}</p>
                                </div>
                              )}
                              {step.args && Object.keys(step.args).length > 0 && (
                                <div>
                                  <p className="text-xs text-blue-400 font-medium mb-0.5">Args</p>
                                  <pre className="text-xs text-slate-400 bg-slate-900 p-2 rounded overflow-x-auto">
                                    {JSON.stringify(step.args, null, 2)}
                                  </pre>
                                </div>
                              )}
                              {step.observation && (
                                <div>
                                  <p className="text-xs text-green-400 font-medium mb-0.5">Observation</p>
                                  <p className="text-xs text-slate-300 whitespace-pre-wrap">{step.observation}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                      {agentResult.dry_run && (
                        <p className="text-xs text-yellow-500 flex items-center gap-1 mt-2">
                          <AlertTriangle size={10} /> Dry run — no actions executed
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Audit Log */}
              {auditLogs.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                  <p className="text-xs text-slate-500 font-medium mb-3 uppercase tracking-wider">Audit Trail</p>
                  <div className="space-y-2">
                    {auditLogs.map(log => (
                      <div key={log.id} className="flex items-start gap-3 text-xs">
                        <span className="text-slate-600 font-mono whitespace-nowrap mt-0.5">
                          {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
                        </span>
                        <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                          {log.action}
                        </span>
                        <span className="text-slate-500">by {log.performed_by}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center flex-1 text-slate-500 text-sm">
              Select an email from the timeline
            </div>
          )}
        </div>

        {/* RIGHT — Contact profile */}
        <div className="w-64 border-l border-slate-800 bg-slate-900/30 overflow-y-auto">
          <div className="p-4 space-y-4">
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-3">Contact Profile</p>
              {contact ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold">
                      {(contact.email || '?')[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white truncate">{contact.email}</p>
                      <p className="text-xs text-slate-500">{contact.company || 'Unknown company'}</p>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {[
                      { label: 'Status', value: contact.status },
                      { label: 'Account Value', value: `$${(contact.account_value || 0).toLocaleString()}` },
                      { label: 'Churn Risk', value: `${((contact.churn_risk_score || 0) * 100).toFixed(0)}%` },
                      { label: 'Open Threads', value: contact.thread_summary?.open ?? 0 },
                      { label: 'Escalated', value: contact.thread_summary?.escalated ?? 0 },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex justify-between text-xs">
                        <span className="text-slate-500">{label}</span>
                        <span className={`font-medium ${
                          label === 'Churn Risk' && parseInt(value) > 50 ? 'text-red-400' : 'text-slate-200'
                        }`}>{value}</span>
                      </div>
                    ))}
                  </div>

                  {/* Sentiment history */}
                  {contact.sentiment_summary?.moving_average !== null && (
                    <div className="pt-3 border-t border-slate-800">
                      <p className="text-xs text-slate-500 mb-2">Sentiment Trend</p>
                      <div className="flex items-center gap-2">
                        <SentimentBadge score={contact.sentiment_summary?.moving_average} />
                        <span className="text-xs text-slate-500">avg</span>
                      </div>
                      <div className="mt-2 flex gap-1">
                        {(contact.sentiment_summary?.recent_scores || []).map((s, i) => (
                          <div
                            key={i}
                            className="flex-1 rounded-sm"
                            style={{
                              height: '24px',
                              backgroundColor: s.sentiment_score >= 0.3 ? '#22c55e33' : s.sentiment_score >= -0.3 ? '#eab30833' : '#ef444433',
                              border: `1px solid ${s.sentiment_score >= 0.3 ? '#22c55e' : s.sentiment_score >= -0.3 ? '#eab308' : '#ef4444'}40`
                            }}
                            title={`${s.message_id}: ${s.sentiment_score}`}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-500">Contact not found</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}