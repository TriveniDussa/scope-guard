import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Projects() {
  const { authFetch } = useAuth()
  const [projects, setProjects] = useState([])
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [notification, setNotification] = useState(null)

  // Form state
  const [projectName, setProjectName] = useState('')
  const [selectedClientId, setSelectedClientId] = useState('')
  const [projectStatus, setProjectStatus] = useState('Active')
  const [editingProject, setEditingProject] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Filter state
  const [filterClient, setFilterClient] = useState('All')
  const [filterStatus, setFilterStatus] = useState('All')

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 3500)
  }

  // Fetch Clients
  const fetchClients = async () => {
    try {
      const res = await authFetch('/clients')
      if (res.ok) {
        const data = await res.json()
        setClients(data)
        if (data.length > 0 && !selectedClientId) {
          setSelectedClientId(data[0].id)
        }
      }
    } catch (err) {
      console.warn('Error fetching clients for project dropdown:', err)
    }
  }

  // Fetch Projects
  const fetchProjects = async () => {
    setLoading(true)
    try {
      const res = await authFetch('/projects')
      if (res.ok) {
        const data = await res.json()
        setProjects(data)
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Failed to load projects', 'error')
      }
    } catch (err) {
      console.warn('Error fetching projects:', err)
      showNotification('Could not connect to projects service', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClients()
    fetchProjects()
  }, [])

  // Create or Update Project
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!projectName.trim()) {
      showNotification('Project name is required', 'error')
      return
    }
    if (!selectedClientId) {
      showNotification('Please select a client for this project', 'error')
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        name: projectName.trim(),
        client_id: selectedClientId,
        status: projectStatus,
      }

      if (editingProject) {
        const res = await authFetch(`/projects/${editingProject.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (res.ok) {
          showNotification('Project updated successfully')
          handleCancelEdit()
          fetchProjects()
        } else {
          const err = await res.json().catch(() => ({}))
          showNotification(err.detail || 'Failed to update project', 'error')
        }
      } else {
        const res = await authFetch('/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (res.ok) {
          showNotification('Project created successfully')
          setProjectName('')
          setProjectStatus('Active')
          fetchProjects()
        } else {
          const err = await res.json().catch(() => ({}))
          showNotification(err.detail || 'Failed to create project', 'error')
        }
      }
    } catch (err) {
      showNotification('Network error while saving project', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleEdit = (project) => {
    setEditingProject(project)
    setProjectName(project.name)
    setSelectedClientId(project.client_id)
    setProjectStatus(project.status)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelEdit = () => {
    setEditingProject(null)
    setProjectName('')
    setProjectStatus('Active')
    if (clients.length > 0) {
      setSelectedClientId(clients[0].id)
    }
  }

  const handleDelete = async (projectId, projectTitle) => {
    if (!window.confirm(`Are you sure you want to delete project "${projectTitle}"? All scope baselines and tasks will also be deleted.`)) {
      return
    }

    try {
      const res = await authFetch(`/projects/${projectId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        showNotification(`Project "${projectTitle}" deleted`)
        if (editingProject?.id === projectId) {
          handleCancelEdit()
        }
        fetchProjects()
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Failed to delete project', 'error')
      }
    } catch (err) {
      showNotification('Network error while deleting project', 'error')
    }
  }

  // Filter projects
  const filteredProjects = projects.filter((p) => {
    const matchesClient = filterClient === 'All' || p.client_id === filterClient
    const matchesStatus = filterStatus === 'All' || p.status === filterStatus
    return matchesClient && matchesStatus
  })

  const getClientName = (clientId) => {
    const client = clients.find((c) => c.id === clientId)
    return client ? client.name : 'Client'
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl border text-sm font-medium shadow-2xl flex items-center gap-3 transition-all transform animate-bounce ${
            notification.type === 'error'
              ? 'bg-rose-950/90 border-rose-800 text-rose-200'
              : 'bg-emerald-950/90 border-emerald-800 text-emerald-200'
          }`}
        >
          <span>{notification.type === 'error' ? '⚠️' : '✓'}</span>
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-indigo-400 font-semibold mb-2">
            <span>📁</span> Engagements & SOW Baselines
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            Project <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Management</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Organize agency client projects, track status, and attach contractual scopes of work.
          </p>
        </div>

        <div className="text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 flex items-center gap-2 self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
          <span>Total Projects: <strong className="text-white">{projects.length}</strong></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Create / Edit Form (5 cols) */}
        <div className="lg:col-span-5">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur sticky top-24">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${editingProject ? 'bg-amber-400' : 'bg-indigo-500'}`}></span>
              {editingProject ? 'Edit Project' : 'Create New Project'}
            </h3>

            {clients.length === 0 ? (
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-2">
                <p className="font-semibold">⚠️ No clients found in workspace.</p>
                <p>Every project must be attached to an existing client. Please add a client first.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Select Client *
                  </label>
                  <select
                    value={selectedClientId}
                    onChange={(e) => setSelectedClientId(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                  >
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Project Name *
                  </label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="e.g. Website Redesign & CMS"
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                    Project Status
                  </label>
                  <select
                    value={projectStatus}
                    onChange={(e) => setProjectStatus(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                  >
                    <option value="Active">Active (In Delivery)</option>
                    <option value="Done">Done (Completed)</option>
                  </select>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  {editingProject && (
                    <button
                      type="button"
                      onClick={handleCancelEdit}
                      className="w-1/3 py-2.5 px-4 rounded-xl text-xs font-semibold text-slate-400 bg-slate-800 hover:bg-slate-700 transition"
                    >
                      Cancel
                    </button>
                  )}
                  <button
                    type="submit"
                    disabled={submitting || !projectName.trim()}
                    className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold text-white transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex items-center justify-center gap-2 ${
                      editingProject
                        ? 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/30'
                        : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/30'
                    }`}
                  >
                    {submitting ? (
                      <span>Saving...</span>
                    ) : editingProject ? (
                      <span>Update Project</span>
                    ) : (
                      <span>+ Create Project</span>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Right Column: Project Listing & Filters (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Client:</span>
              <select
                value={filterClient}
                onChange={(e) => setFilterClient(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
              >
                <option value="All">All Clients</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-400">Status:</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
              >
                <option value="All">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Done">Done</option>
              </select>
              <button
                onClick={fetchProjects}
                className="p-1 text-slate-400 hover:text-slate-200 transition ml-1"
                title="Refresh projects"
              >
                ↻
              </button>
            </div>
          </div>

          {/* List */}
          {loading ? (
            <div className="py-16 text-center text-xs text-slate-500">Loading projects...</div>
          ) : filteredProjects.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
              <p className="text-slate-400 text-sm">No projects found matching filter.</p>
              <p className="text-xs text-slate-500 mt-1">Create your first client project on the left.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredProjects.map((project) => (
                <div
                  key={project.id}
                  className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {getClientName(project.client_id)}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          project.status === 'Done'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                        }`}
                      >
                        {project.status}
                      </span>
                    </div>
                    <h4 className="text-base font-semibold text-white truncate">{project.name}</h4>
                    <span className="text-[11px] text-slate-500 block mt-1">
                      Created: {new Date(project.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <button
                      onClick={() => handleEdit(project)}
                      className="px-3 py-1 text-xs font-medium text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-md border border-indigo-500/30 transition"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(project.id, project.name)}
                      className="px-3 py-1 text-xs font-medium text-rose-400 bg-rose-500/10 hover:bg-rose-500/20 rounded-md border border-rose-500/30 transition"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
