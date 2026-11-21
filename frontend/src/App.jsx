import React, { useState } from 'react'
import ScopeOfWork from './pages/ScopeOfWork'
import Tasks from './pages/Tasks'
import RequestChecker from './pages/RequestChecker'

function App() {
  const [activeTab, setActiveTab] = useState('request-checker')
  const [token, setToken] = useState(null)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 w-full flex items-center justify-between py-3.5">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('request-checker')}>
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
              SG
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white leading-tight">SCOPE GUARD</h1>
              <p className="text-xs text-slate-400">AI-Powered Scope of Work & Task Management</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800">
            <button
              onClick={() => setActiveTab('request-checker')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'request-checker'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              AI Request Checker
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'tasks'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Tasks
            </button>
            <button
              onClick={() => setActiveTab('scope-of-work')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'scope-of-work'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Scope of Work
            </button>
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === 'overview'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              System Overview
            </button>
          </nav>

          <div className="hidden sm:flex items-center gap-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Day 8 Live
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              AI Checker
            </span>
          </div>
        </div>
      </header>

      {/* Main View Area */}
      <main className="flex-1">
        {activeTab === 'request-checker' && <RequestChecker token={token} />}

        {activeTab === 'tasks' && <Tasks token={token} />}

        {activeTab === 'scope-of-work' && <ScopeOfWork token={token} />}

        {activeTab === 'overview' && (
          <div className="max-w-4xl mx-auto w-full text-center py-16 px-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-400 mb-6">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Day 7: Task Management & Scope Linking Active
            </div>
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
              Scope-Driven <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Sprint Execution</span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-8">
              Every task is strictly attached to an approved deliverable scope item.
              Prevent phantom tasks and unauthorized work that burns agency margins.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto text-left">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <p className="text-xs text-slate-500 uppercase font-semibold">Backend</p>
                <p className="text-sm font-semibold text-slate-200 mt-1">FastAPI + Python 3.12</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <p className="text-xs text-slate-500 uppercase font-semibold">Database</p>
                <p className="text-sm font-semibold text-slate-200 mt-1">PostgreSQL (Supabase)</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <p className="text-xs text-slate-500 uppercase font-semibold">Task Linking</p>
                <p className="text-sm font-semibold text-slate-200 mt-1">Scope Item Enforced</p>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                <p className="text-xs text-slate-500 uppercase font-semibold">Frontend</p>
                <p className="text-sm font-semibold text-slate-200 mt-1">React 19 + Tailwind v4</p>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-center gap-4">
              <button
                onClick={() => setActiveTab('tasks')}
                className="px-6 py-3 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-lg shadow-indigo-500/30 transition"
              >
                Open Tasks Page &rarr;
              </button>
              <button
                onClick={() => setActiveTab('scope-of-work')}
                className="px-6 py-3 text-sm font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-xl border border-slate-700 transition"
              >
                View Scope of Work
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 px-4 text-center text-xs text-slate-500">
        Scope Guard &copy; 2026 &bull; Multi-Tenant Agency Scope Control
      </footer>
    </div>
  )
}

export default App
