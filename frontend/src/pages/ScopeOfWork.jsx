import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/v1'

export default function ScopeOfWork({ token, currentWorkspace }) {
  const [projects, setProjects] = useState([
    { id: '11111111-1111-1111-1111-111111111111', name: 'Website Redesign', status: 'Active' },
    { id: '22222222-2222-2222-2222-222222222222', name: 'Mobile App Refresh', status: 'Active' },
  ])
  const [selectedProjectId, setSelectedProjectId] = useState('11111111-1111-1111-1111-111111111111')
  
  const [scopeItems, setScopeItems] = useState([
    {
      id: 'item-demo-1',
      project_id: '11111111-1111-1111-1111-111111111111',
      included_description: 'Home page design, five pages, contact form.',
      not_included_description: 'Hindi language version, payment gateway integration.',
      created_at: new Date().toISOString(),
    },
    {
      id: 'item-demo-2',
      project_id: '11111111-1111-1111-1111-111111111111',
      included_description: 'Standard responsive layout for desktop and tablet.',
      not_included_description: 'Custom native iOS / Android tablet wrapper app.',
      created_at: new Date().toISOString(),
    },
  ])

  const [includedText, setIncludedText] = useState('')
  const [notIncludedText, setNotIncludedText] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [notification, setNotification] = useState(null)

  // Fetch projects from backend if token is available
  useEffect(() => {
    if (!token) return
    const fetchProjects = async () => {
      try {
        const res = await fetch(`${API_BASE}/projects`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          if (data.length > 0) {
            setProjects(data)
            setSelectedProjectId(data[0].id)
          }
        }
      } catch (err) {
        console.warn('API unavailable or offline, using demo data', err)
      }
    }
    fetchProjects()
  }, [token])

  // Fetch scope items for selected project
  useEffect(() => {
    if (!token || !selectedProjectId) return
    const fetchScopeItems = async () => {
      try {
        setLoading(true)
        const res = await fetch(`${API_BASE}/scope-items?project_id=${selectedProjectId}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          setScopeItems(data)
        }
      } catch (err) {
        console.warn('API error, keeping current state', err)
      } finally {
        setLoading(false)
      }
    }
    fetchScopeItems()
  }, [selectedProjectId, token])

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 3500)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!includedText.trim() || !notIncludedText.trim()) {
      showNotification('Please fill in both Included and Not Included descriptions.', 'error')
      return
    }

    setLoading(true)
    try {
      if (editingId) {
        // Update existing item
        if (token) {
          const res = await fetch(`${API_BASE}/scope-items/${editingId}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              included_description: includedText.trim(),
              not_included_description: notIncludedText.trim(),
            }),
          })
          if (!res.ok) throw new Error('Failed to update scope item')
          const updated = await res.json()
          setScopeItems((prev) => prev.map((item) => (item.id === editingId ? updated : item)))
        } else {
          setScopeItems((prev) =>
            prev.map((item) =>
              item.id === editingId
                ? {
                    ...item,
                    included_description: includedText.trim(),
                    not_included_description: notIncludedText.trim(),
                    updated_at: new Date().toISOString(),
                  }
                : item
            )
          )
        }
        showNotification('Scope item updated successfully!')
        setEditingId(null)
      } else {
        // Create new item
        if (token) {
          const res = await fetch(`${API_BASE}/scope-items`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
              project_id: selectedProjectId,
              included_description: includedText.trim(),
              not_included_description: notIncludedText.trim(),
            }),
          })
          if (!res.ok) throw new Error('Failed to create scope item')
          const created = await res.json()
          setScopeItems((prev) => [created, ...prev])
        } else {
          const newItem = {
            id: `item-${Date.now()}`,
            project_id: selectedProjectId,
            included_description: includedText.trim(),
            not_included_description: notIncludedText.trim(),
            created_at: new Date().toISOString(),
          }
          setScopeItems((prev) => [newItem, ...prev])
        }
        showNotification('Scope item added to project scope baseline!')
      }

      setIncludedText('')
      setNotIncludedText('')
    } catch (err) {
      showNotification(err.message || 'Error saving scope item', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (item) => {
    setEditingId(item.id)
    setIncludedText(item.included_description)
    setNotIncludedText(item.not_included_description)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setIncludedText('')
    setNotIncludedText('')
  }

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this Scope of Work item?')) return
    setLoading(true)
    try {
      if (token) {
        const res = await fetch(`${API_BASE}/scope-items/${id}`, {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error('Failed to delete scope item')
      }
      setScopeItems((prev) => prev.filter((item) => item.id !== id))
      showNotification('Scope item deleted.')
      if (editingId === id) handleCancelEdit()
    } catch (err) {
      showNotification(err.message || 'Error deleting item', 'error')
    } finally {
      setLoading(false)
    }
  }

  const filteredItems = scopeItems.filter(
    (item) => !selectedProjectId || item.project_id === selectedProjectId
  )

  const activeProject = projects.find((p) => p.id === selectedProjectId)

  return (
    <div className="max-w-6xl mx-auto w-full px-4 py-8">
      {/* Notification banner */}
      {notification && (
        <div
          className={`mb-6 p-4 rounded-xl text-sm font-medium flex items-center justify-between border ${
            notification.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          <span>{notification.msg}</span>
          <button
            onClick={() => setNotification(null)}
            className="text-xs opacity-70 hover:opacity-100"
          >
            ✕
          </button>
        </div>
      )}

      {/* Header & Project Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            Contractual Scope Definition
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Scope of Work (SOW)</h2>
          <p className="text-sm text-slate-400 mt-1">
            Establish non-negotiable boundaries: explicit deliverables versus out-of-scope exclusions.
          </p>
        </div>

        {/* Project Dropdown */}
        <div className="flex items-center gap-3">
          <label htmlFor="project-select" className="text-xs uppercase font-semibold text-slate-400">
            Project:
          </label>
          <select
            id="project-select"
            value={selectedProjectId}
            onChange={(e) => {
              setSelectedProjectId(e.target.value)
              if (editingId) handleCancelEdit()
            }}
            className="bg-slate-900 border border-slate-700 text-slate-100 text-sm rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.status})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Scope Item Creation / Edit Form */}
      <form onSubmit={handleSave} className="mt-8 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
            {editingId ? 'Edit Scope Item' : 'Add New Scope of Work Item'}
          </h3>
          {activeProject && (
            <span className="text-xs text-slate-400">
              For: <strong className="text-slate-200">{activeProject.name}</strong>
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 1. Included Text Area */}
          <div className="flex flex-col">
            <label className="text-xs uppercase font-bold text-emerald-400 mb-2 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              Included Deliverables
            </label>
            <textarea
              rows={4}
              value={includedText}
              onChange={(e) => setIncludedText(e.target.value)}
              placeholder="e.g. Home page design, five pages, contact form."
              className="w-full bg-slate-950 border border-emerald-500/30 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition"
            />
            <p className="text-xs text-slate-500 mt-1.5">
              Specific contracted deliverables promised to the client.
            </p>
          </div>

          {/* 2. Not Included Text Area */}
          <div className="flex flex-col">
            <label className="text-xs uppercase font-bold text-rose-400 mb-2 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-400"></span>
              Not Included (Out of Scope)
            </label>
            <textarea
              rows={4}
              value={notIncludedText}
              onChange={(e) => setNotIncludedText(e.target.value)}
              placeholder="e.g. Hindi language version, payment gateway integration."
              className="w-full bg-slate-950 border border-rose-500/30 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:border-transparent transition"
            />
            <p className="text-xs text-slate-500 mt-1.5">
              Explicit exclusions used by the AI Request Checker to reject creep.
            </p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-slate-800">
          {editingId && (
            <button
              type="button"
              onClick={handleCancelEdit}
              className="px-4 py-2 text-sm font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg transition"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-lg shadow-indigo-500/30 transition disabled:opacity-50"
          >
            {loading ? 'Saving...' : editingId ? 'Update Scope Item' : 'Save Scope Item'}
          </button>
        </div>
      </form>

      {/* Scope Item Listing */}
      <div className="mt-12">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            Scope Items Listing
            <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400">
              {filteredItems.length} items
            </span>
          </h3>
        </div>

        {filteredItems.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
            <p className="text-slate-400 text-sm">No Scope of Work items created for this project yet.</p>
            <p className="text-xs text-slate-500 mt-1">Use the form above to add your first included & excluded scope baseline.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredItems.map((item, idx) => (
              <div
                key={item.id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-indigo-600/20 text-indigo-400 text-xs font-bold flex items-center justify-center">
                      #{idx + 1}
                    </span>
                    <span className="text-xs text-slate-400">
                      ID: <code className="text-xs text-slate-300">{item.id.slice(0, 8)}...</code>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(item)}
                      className="px-3 py-1 text-xs font-medium text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-md border border-indigo-500/30 transition"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="px-3 py-1 text-xs font-medium text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 rounded-md border border-rose-500/30 transition"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {/* Displaying Both Fields Separately */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                  {/* Included Section */}
                  <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20">
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                      Included Deliverables
                    </p>
                    <p className="text-sm text-slate-200 whitespace-pre-line leading-relaxed">
                      {item.included_description}
                    </p>
                  </div>

                  {/* Not Included Section */}
                  <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-500/20">
                    <p className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                      Not Included (Out of Scope)
                    </p>
                    <p className="text-sm text-slate-200 whitespace-pre-line leading-relaxed">
                      {item.not_included_description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
