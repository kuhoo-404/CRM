import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchStats, fetchCategoryBreakdown, fetchThreads, fetchSentimentTrend } from '../api/client'
import { ArrowLeft, TrendingDown, AlertTriangle } from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend, BarChart, Bar
} from 'recharts'

const COLORS = ['#3b82f6', '#ef4444', '#8b5cf6', '#f59e0b', '#10b981', '#ec4899', '#06b6d4', '#84cc16']

export default function Analytics() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [breakdown, setBreakdown] = useState([])
  const [threads, setThreads] = useState([])
  const [sentimentData, setSentimentData] = useState([])
  const [selectedSender, setSelectedSender] = useState('karen.w@retail-co.com')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [s, b, t] = await Promise.all([
          fetchStats(),
          fetchCategoryBreakdown(0),
          fetchThreads(),
        ])
        setStats(s)
        setBreakdown(b?.breakdown || [])
        setThreads(t || [])
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    if (!selectedSender) return
    fetchSentimentTrend(selectedSender, 0)
      .then(data => {
        const points = (data?.trend || []).map(p => ({
          date: p.timestamp ? new Date(p.timestamp).toLocaleDateString() : '',
          score: p.sentiment_score,
          category: p.category,
        }))
        setSentimentData(points)
      })
      .catch(() => setSentimentData([]))
  }, [selectedSender])

  // Agent performance metrics from stats
  const totalClassified = stats ? (stats.total - stats.spam - (stats.pending || 0)) : 0
  const autoReplyRate = totalClassified > 0 ? ((stats?.replied || 0) / totalClassified * 100).toFixed(1) : 0
  const escalationRate = totalClassified > 0 ? ((stats?.escalated || 0) / totalClassified * 100).toFixed(1) : 0

  // At-risk accounts: threads with open status
  const atRisk = threads
    .filter(t => t.status === 'Open' && t.email_count >= 2)
    .slice(0, 5)

  // Bar chart data from stats
  const statusData = stats ? [
    { name: 'Pending', value: stats.pending || 0, fill: '#3b82f6' },
    { name: 'Replied', value: stats.replied || 0, fill: '#22c55e' },
    { name: 'Escalated', value: stats.escalated || 0, fill: '#ef4444' },
    { name: 'Spam', value: stats.spam || 0, fill: '#64748b' },
    { name: 'Critical', value: stats.critical || 0, fill: '#dc2626' },
  ] : []

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500">
      Loading analytics...
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-1.5 rounded-lg hover:bg-slate-800 transition-colors">
          <ArrowLeft size={16} className="text-slate-400" />
        </button>
        <div>
          <h1 className="text-lg font-bold text-white">Analytics Dashboard</h1>
          <p className="text-xs text-slate-500">System performance and email intelligence</p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Agent performance row */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: 'Auto-Reply Rate', value: `${autoReplyRate}%`, sub: `${stats?.replied || 0} emails`, color: 'text-green-400' },
            { label: 'Escalation Rate', value: `${escalationRate}%`, sub: `${stats?.escalated || 0} emails`, color: 'text-orange-400' },
            { label: 'Security Threats', value: stats?.security_threats || 0, sub: 'blocked, never replied', color: 'text-red-400' },
            { label: 'Needs Human', value: stats?.requires_human || 0, sub: 'awaiting review', color: 'text-yellow-400' },
          ].map(card => (
            <div key={card.label} className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-1">{card.label}</p>
              <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
              <p className="text-xs text-slate-600 mt-1">{card.sub}</p>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Category pie */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Category Distribution</h3>
            {breakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={breakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    dataKey="count"
                    nameKey="category"
                    label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {breakdown.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#94a3b8' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center text-slate-500 text-sm">
                No classified emails yet
              </div>
            )}
          </div>

          {/* Status bar chart */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Email Status Breakdown</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statusData} barSize={32}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {statusData.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Sentiment trend */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Sentiment Trend</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Sender:</span>
              <select
                value={selectedSender}
                onChange={e => setSelectedSender(e.target.value)}
                className="text-xs bg-slate-800 border border-slate-700 rounded-lg px-2 py-1 text-slate-300 focus:outline-none focus:border-blue-500"
              >
                {['karen.w@retail-co.com', 'bob.jones@enterprise.net', 'alice.smith@greenlight-npo.org',
                  'marcus.del@fintech-startup.co', 'user.confused@hotmail.com'].map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
          {sentimentData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[-1, 1]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#94a3b8' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
                {/* Zero line reference */}
                <Line dataKey={() => 0} stroke="#334155" strokeDasharray="4 4" dot={false} strokeWidth={1} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[180px] flex items-center justify-center text-slate-500 text-sm">
              No sentiment data for this sender
            </div>
          )}
        </div>

        {/* At-risk accounts */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle size={14} className="text-orange-400" />
            At-Risk Accounts
          </h3>
          {atRisk.length > 0 ? (
            <div className="space-y-2">
              {atRisk.map(t => (
                <div key={t.thread_id}
                  onClick={() => navigate(`/thread/${encodeURIComponent(t.sender_email)}`)}
                  className="flex items-center justify-between p-3 bg-slate-800/40 border border-slate-700/50 rounded-lg cursor-pointer hover:bg-slate-800/60 transition-colors"
                >
                  <div>
                    <p className="text-sm text-slate-200">{t.sender_email}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{t.subject}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">{t.email_count} emails</span>
                    <TrendingDown size={14} className="text-red-400" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No at-risk accounts detected</p>
          )}
        </div>
      </div>
    </div>
  )
}