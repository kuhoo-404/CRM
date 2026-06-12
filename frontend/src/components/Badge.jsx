export function UrgencyBadge({ urgency }) {
  const map = {
    Critical: 'bg-red-500/20 text-red-400 border border-red-500/40',
    High: 'bg-orange-500/20 text-orange-400 border border-orange-500/40',
    Medium: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40',
    Low: 'bg-green-500/20 text-green-400 border border-green-500/40',
  }
  if (!urgency) return null
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[urgency] || 'bg-slate-700 text-slate-300'}`}>
      {urgency}
    </span>
  )
}

export function CategoryBadge({ category }) {
  const map = {
    Complaint: 'bg-red-900/40 text-red-300',
    Inquiry: 'bg-blue-900/40 text-blue-300',
    'Bug Report': 'bg-purple-900/40 text-purple-300',
    'Feature Request': 'bg-cyan-900/40 text-cyan-300',
    Compliance: 'bg-yellow-900/40 text-yellow-300',
    Legal: 'bg-red-900/60 text-red-200',
    Billing: 'bg-emerald-900/40 text-emerald-300',
    Spam: 'bg-slate-700 text-slate-400',
    Internal: 'bg-indigo-900/40 text-indigo-300',
    Other: 'bg-slate-700 text-slate-300',
  }
  if (!category) return <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-500">unclassified</span>
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium ${map[category] || 'bg-slate-700 text-slate-300'}`}>
      {category}
    </span>
  )
}

export function SentimentBadge({ score }) {
  if (score === null || score === undefined) return null
  const color = score >= 0.3 ? 'text-green-400' : score >= -0.3 ? 'text-yellow-400' : 'text-red-400'
  const bg = score >= 0.3 ? 'bg-green-500/10' : score >= -0.3 ? 'bg-yellow-500/10' : 'bg-red-500/10'
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-mono font-medium ${color} ${bg}`}>
      {score > 0 ? '+' : ''}{score.toFixed(2)}
    </span>
  )
}

export function StatusBadge({ status }) {
  const map = {
    Received: 'bg-blue-500/20 text-blue-300',
    Processing: 'bg-yellow-500/20 text-yellow-300',
    Replied: 'bg-green-500/20 text-green-300',
    Escalated: 'bg-red-500/20 text-red-300',
    Ignored: 'bg-slate-700 text-slate-400',
  }
  if (!status) return null
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium ${map[status] || 'bg-slate-700 text-slate-300'}`}>
      {status}
    </span>
  )
}