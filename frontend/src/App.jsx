import React from 'react'

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-6">
      <header className="max-w-6xl mx-auto w-full flex items-center justify-between py-4 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/30">
            SG
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">SCOPE GUARD</h1>
            <p className="text-xs text-slate-400">AI-Powered Scope & Task Control</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            API v1 Ready
          </span>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            Multi-Tenant
          </span>
        </div>
      </header>

      <main className="max-w-4xl mx-auto w-full my-auto text-center py-16">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-400 mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Initial Setup & Database Architecture Initialized
        </div>
        <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white mb-4">
          Defend Agency Margins Against <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Scope Creep</span>
        </h2>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-8">
          Full multi-tenant architecture with isolated workspaces, JWT authentication,
          PostgreSQL schema with 8 core entities, and AI-powered scope protection.
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
            <p className="text-xs text-slate-500 uppercase font-semibold">Auth & Isolation</p>
            <p className="text-sm font-semibold text-slate-200 mt-1">JWT + Strict Workspace</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <p className="text-xs text-slate-500 uppercase font-semibold">Frontend</p>
            <p className="text-sm font-semibold text-slate-200 mt-1">React + Vite + Tailwind</p>
          </div>
        </div>
      </main>

      <footer className="max-w-6xl mx-auto w-full py-4 text-center text-xs text-slate-500 border-t border-slate-800">
        Scope Guard &copy; 2026 &bull; Production Architecture Ready
      </footer>
    </div>
  )
}

export default App
