import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Dashboard({ onNavigate }) {
  const { user, workspace, authFetch } = useAuth()
  const [stats, setStats] = useState({
    clients: 0,
    projects: 0,
    scopeItems: 0,
    tasks: 0,
    requests: 0,
    lessons: 0,
  })
  const [recentRequests, setRecentRequests] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true)
      try {
        const [cRes, pRes, sRes, tRes, rRes, lRes] = await Promise.all([
          authFetch('/clients'),
          authFetch('/projects'),
          authFetch('/scope-items'),
          authFetch('/tasks'),
          authFetch('/requests'),
          authFetch('/lessons'),
        ])

        const [cData, pData, sData, tData, rData, lData] = await Promise.all([
          cRes.ok ? cRes.json() : [],
          pRes.ok ? pRes.json() : [],
          sRes.ok ? sRes.json() : [],
          tRes.ok ? tRes.json() : [],
          rRes.ok ? rRes.json() : [],
          lRes.ok ? lRes.json() : [],
        ])

        setStats({
          clients: cData.length,
          projects: pData.length,
          scopeItems: sData.length,
          tasks: tData.length,
          requests: rData.length,
          lessons: lData.length,
        })

        setRecentRequests(rData.slice(0, 5))
      } catch (err) {
        console.warn('Dashboard fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-semibold text-indigo-400 mb-3">
              <span>🛡️</span> Multi-Tenant Agency Operations Live
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">
              Welcome back, <span className="text-indigo-400">{user?.full_name || 'Agency Admin'}</span>
            </h2>
            <p className="text-slate-400 text-sm mt-1 max-w-xl">
              Workspace: <strong className="text-slate-200">{workspace?.name || 'Agency Workspace'}</strong> &bull; Protect agency profit margins through automated scope control and AI sprint validation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('request-checker')}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 transition flex items-center gap-2"
            >
              <span>✨ Check New Request</span>
            </button>
            <button
              onClick={() => onNavigate('scope-of-work')}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
            >
              Manage SOWs
            </button>
          </div>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Clients</p>
          <p className="text-2xl font-bold text-white mt-1">{loading ? '...' : stats.clients}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Active Accounts</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Projects</p>
          <p className="text-2xl font-bold text-white mt-1">{loading ? '...' : stats.projects}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Active & Done</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Scope Items</p>
          <p className="text-2xl font-bold text-white mt-1">{loading ? '...' : stats.scopeItems}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Agreed Baselines</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Tasks</p>
          <p className="text-2xl font-bold text-white mt-1">{loading ? '...' : stats.tasks}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Deliverable-Linked</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">AI Evaluated</p>
          <p className="text-2xl font-bold text-indigo-400 mt-1">{loading ? '...' : stats.requests}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Client Requests</span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 backdrop-blur">
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Lessons</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">{loading ? '...' : stats.lessons}</p>
          <span className="text-[11px] text-slate-500 mt-1 block">Continuous Rules</span>
        </div>
      </div>

      {/* Quick Launchpad & Recent AI Requests */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Quick Launchpad (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur space-y-3">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <span>⚡</span> Agency Control Launchpad
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Direct access to all agency management operations:
            </p>

            <button
              onClick={() => onNavigate('clients')}
              className="w-full p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 transition flex items-center justify-between text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-slate-200 group-hover:text-indigo-400 transition">
                  1. Manage Clients &rarr;
                </p>
                <p className="text-xs text-slate-500">Create client profiles and primary contact addresses</p>
              </div>
              <span className="text-slate-600 group-hover:text-indigo-400 transition">🏢</span>
            </button>

            <button
              onClick={() => onNavigate('projects')}
              className="w-full p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 transition flex items-center justify-between text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-slate-200 group-hover:text-indigo-400 transition">
                  2. Manage Projects &rarr;
                </p>
                <p className="text-xs text-slate-500">Establish Active or Done client projects</p>
              </div>
              <span className="text-slate-600 group-hover:text-indigo-400 transition">📁</span>
            </button>

            <button
              onClick={() => onNavigate('scope-of-work')}
              className="w-full p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 transition flex items-center justify-between text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-slate-200 group-hover:text-indigo-400 transition">
                  3. Define Scope of Work &rarr;
                </p>
                <p className="text-xs text-slate-500">Document Included deliverables and Not Included exclusions</p>
              </div>
              <span className="text-slate-600 group-hover:text-indigo-400 transition">📝</span>
            </button>

            <button
              onClick={() => onNavigate('tasks')}
              className="w-full p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-indigo-500/50 transition flex items-center justify-between text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-slate-200 group-hover:text-indigo-400 transition">
                  4. Track Sprint Tasks &rarr;
                </p>
                <p className="text-xs text-slate-500">Strictly link sprint work to agreed deliverables</p>
              </div>
              <span className="text-slate-600 group-hover:text-indigo-400 transition">✓</span>
            </button>

            <button
              onClick={() => onNavigate('request-checker')}
              className="w-full p-3 rounded-xl bg-indigo-950/20 border border-indigo-900/50 hover:border-indigo-500 transition flex items-center justify-between text-left group"
            >
              <div>
                <p className="text-sm font-semibold text-indigo-300 group-hover:text-indigo-200 transition">
                  5. AI Request Checker & Lessons &rarr;
                </p>
                <p className="text-xs text-indigo-400/80">Classify incoming scope changes with Gemini 1.5 Flash</p>
              </div>
              <span className="text-indigo-400">✨</span>
            </button>
          </div>
        </div>

        {/* Recent AI Activity (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>🛡️</span> Recent AI Scope Evaluations
              </h3>
              <button
                onClick={() => onNavigate('request-checker')}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition"
              >
                View All &rarr;
              </button>
            </div>

            {loading ? (
              <div className="py-12 text-center text-xs text-slate-500">Loading recent evaluations...</div>
            ) : recentRequests.length === 0 ? (
              <div className="py-12 text-center border border-dashed border-slate-800 rounded-xl">
                <p className="text-sm text-slate-400">No requests evaluated yet in this workspace.</p>
                <p className="text-xs text-slate-500 mt-1">
                  Navigate to the AI Request Checker to test client scope evaluation.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentRequests.map((req) => (
                  <div
                    key={req.id}
                    className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[11px] font-semibold text-slate-300">
                          {req.project_name || 'Project'}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                            req.classification === 'In scope'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : req.classification === 'Out of scope'
                              ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          }`}
                        >
                          {req.classification}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 truncate">"{req.client_request}"</p>
                    </div>

                    <span className="text-[11px] text-slate-500 shrink-0">
                      {new Date(req.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
