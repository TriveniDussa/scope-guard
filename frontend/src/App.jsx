import React, { useState } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Clients from './pages/Clients'
import Projects from './pages/Projects'
import ScopeOfWork from './pages/ScopeOfWork'
import Tasks from './pages/Tasks'
import RequestChecker from './pages/RequestChecker'
import Dashboard from './pages/Dashboard'

function AppContent() {
  const { isAuthenticated, user, workspace, logout, loading } = useAuth()
  const [activeTab, setActiveTab] = useState('overview')
  const [showSignup, setShowSignup] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center text-slate-300">
        <div className="w-12 h-12 rounded-2xl bg-indigo-600 animate-pulse flex items-center justify-center font-bold text-white shadow-xl shadow-indigo-500/30 text-xl mb-4">
          SG
        </div>
        <div className="text-sm font-medium animate-pulse text-slate-400">Restoring Scope Guard session...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return showSignup ? (
      <Signup onSwitchToLogin={() => setShowSignup(false)} />
    ) : (
      <Login onSwitchToSignup={() => setShowSignup(true)} />
    )
  }

  const navItems = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'clients', label: 'Clients', icon: '👥' },
    { id: 'projects', label: 'Projects', icon: '📁' },
    { id: 'scope-of-work', label: 'Scope of Work', icon: '📜' },
    { id: 'tasks', label: 'Tasks', icon: '✅' },
    { id: 'request-checker', label: 'AI Request Checker', icon: '🛡️' },
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 w-full flex items-center justify-between py-3">
          {/* Logo & Agency Branding */}
          <div
            className="flex items-center space-x-3 cursor-pointer select-none"
            onClick={() => setActiveTab('overview')}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center font-extrabold text-white shadow-lg shadow-indigo-500/30">
              SG
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-extrabold tracking-tight text-white leading-tight">SCOPE GUARD</h1>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {workspace?.name || 'Agency Workspace'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">AI-Powered Scope of Work & Task Management</p>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden lg:flex items-center gap-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === item.id
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>

          {/* User Profile & Logout */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-bold text-slate-200 leading-tight">
                {user?.full_name || 'Agency Member'}
              </span>
              <span className="text-[10px] text-slate-400 truncate max-w-[140px]">
                {user?.email}
              </span>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 transition flex items-center gap-1.5"
            >
              <span>Logout</span>
              <span className="text-rose-400">&rarr;</span>
            </button>

            {/* Mobile Hamburger Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200"
            >
              {mobileMenuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-slate-800 bg-slate-950 px-4 py-3 space-y-1">
            <div className="px-2 py-1 mb-2 text-xs font-medium text-slate-400">
              Workspace: <strong className="text-indigo-400">{workspace?.name}</strong>
            </div>
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id)
                  setMobileMenuOpen(false)
                }}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 transition ${
                  activeTab === item.id
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        )}
      </header>

      {/* Main View Area */}
      <main className="flex-1 pb-12">
        {activeTab === 'overview' && <Dashboard onNavigate={(tab) => setActiveTab(tab)} />}
        {activeTab === 'clients' && <Clients />}
        {activeTab === 'projects' && <Projects />}
        {activeTab === 'scope-of-work' && <ScopeOfWork />}
        {activeTab === 'tasks' && <Tasks />}
        {activeTab === 'request-checker' && <RequestChecker />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950 py-4 px-4 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between max-w-7xl mx-auto w-full gap-2">
        <div>SCOPE GUARD &copy; 2026 &bull; Multi-Tenant Agency Scope Control</div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Workspace Isolated: {workspace?.name || 'Default'}
          </span>
          <span className="text-[11px] text-slate-400">Day 10: Complete Browser Application</span>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
