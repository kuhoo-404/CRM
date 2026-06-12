import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchThreads, fetchStats } from '../api/client'
import { UrgencyBadge, CategoryBadge, SentimentBadge, StatusBadge } from '../components/Badge'
import { Search, RefreshCw, AlertTriangle, Shield, Users, CheckCircle, Clock, Mail } from 'lucide-react'

const TABS = ['All', 'Needs Human', 'Escalated', 'Auto-Replied', 'Spam']
const POLL_INTERVAL = 10000

export default function Inbox() {
  const [threads, setThreads] = useState([])
  const [stats, setStats] = useState(null)
  const [activeTab, setActiveTab] = useState('All')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const navigate = useNavigate()

  const load = async () => {
    try {
      const [t, s] = await Promise.all([fetchThreads(), fetchStats()])
      setThreads(t || [])
      setStats(s)
      setLastUpdated(new Date())
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const interval = setInterval(load, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [])

  const filtered = threads.filter(t => {
    const latest = t.latest_email
    const matchSearch = !search ||
      (t.subject || '').toLowerCase().includes(search.toLowerCase()) ||
      (t.sender_email || '').toLowerCase().includes(search.toLowerCase()) ||
      (latest?.body_preview || '').toLowerCase().includes(search.toLowerCase())

    if (!matchSearch) return false

    switch (activeTab) {
      case 'Needs Human': return t.emails?.some(e => e.requires_human) || latest?.requires_human
      case 'Escalated': return t.status === 'Escalated'
      case 'Auto-Replied': return t.status === 'Resolved'
      case 'Spam': return t.emails?.some(e => e.is_spam)
      default: return true
    }
  })

  const statCards = [
    { label: 'Total', value: stats?.total, icon: Mail, color: 'text-blue-400' },
    { label: 'Needs Human', value: stats?.requires_human, icon: Users, color: 'text-orange-400' },
    { label: 'Escalated', value: stats?.escalated, icon: AlertTriangle, color: 'text-red-400' },
    { label: 'Critical', value: stats?.critical, icon: Shield, color: 'text-red-500' },
    { label: 'Replied', value: stats?.replied, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Spam', value: stats?.spam, icon: Clock, color: 'text-slate-400' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">SenAI CRM</h1>
            <p className="text-xs text-slate-500 mt-0.5">Mission Control Inbox</p>
          </div>
          <div className="flex items-center gap-3">
            {lastUpdated && (
              <span className="text-xs text-slate-500">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <button onClick={load} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <RefreshCw size={14} className="text-slate-400" />
            </button>
            <button onClick={() => navigate('/analytics')}
              className="px-3 py-1.5 text-xs rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors">
              Analytics
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-4 space-y-4">
        {/* Stat Cards */}
        <div className="grid grid-cols-6 gap-3">
          {statCards.map(s => (
            <div key={s.label} className="bg-slate-900 border border-slate-800 rounded-xl p-3">
              <div className="flex items-center gap-2 mb-1">
                <s.icon size={14} className={s.color} />
                <span className="text-xs text-slate-400">{s.label}</span>
              </div>
              <div className={`text-2xl font-bold ${s.color}`}>{s.value ?? '—'}</div>
            </div>
          ))}
        </div>

        {/* Search + Tabs */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search emails, subjects, senders..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-900 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1">
            {TABS.map(tab => (
              <button key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 text-xs rounded-md transition-colors font-medium ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}>
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Thread List */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20 text-slate-500">
              <RefreshCw size={16} className="animate-spin mr-2" /> Loading emails...
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center py-20 text-slate-500 text-sm">
              No emails match this filter
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Sender</th>
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Subject</th>
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Category</th>
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Urgency</th>
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Sentiment</th>
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Status</th>
                  <th className="px-4 py-3 text-xs text-slate-500 font-medium">Emails</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((thread, i) => {
                  const latest = thread.latest_email
                  return (
                    <tr
                      key={thread.thread_id}
                      onClick={() => navigate(`/thread/${encodeURIComponent(thread.sender_email)}`)}
                      className={`border-b border-slate-800/50 cursor-pointer hover:bg-slate-800/40 transition-colors ${
                        i % 2 === 0 ? '' : 'bg-slate-900/30'
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-slate-200 truncate max-w-[160px]">
                          {thread.sender_email}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-slate-300 truncate max-w-[220px]">{thread.subject}</div>
                        {latest?.body_preview && (
                          <div className="text-xs text-slate-500 truncate max-w-[220px] mt-0.5">
                            {latest.body_preview}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <CategoryBadge category={latest?.category} />
                      </td>
                      <td className="px-4 py-3">
                        <UrgencyBadge urgency={latest?.urgency} />
                      </td>
                      <td className="px-4 py-3">
                        <SentimentBadge score={latest?.sentiment_score} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={thread.status} />
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">
                          {thread.email_count}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}