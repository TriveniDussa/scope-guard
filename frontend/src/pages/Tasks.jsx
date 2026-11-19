import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/v1'

export default function Tasks({ token }) {
  const [projects, setProjects] = useState([])
  const [selectedProjectId, setSelectedProjectId] = useState('')
  const [scopeItems, setScopeItems] = useState([])
  const [selectedScopeItemId, setSelectedScopeItemId] = useState('')

  const [tasks, setTasks] = useState([])
  const [taskTitle, setTaskTitle] = useState('')
  const [dueDate, setDueDate] = useState('')
  const [taskStatus, setTaskStatus] = useState('To do')
  const [editingId, setEditingId] = useState(null)

  const [loading, setLoading] = useState(false)
  const [notification, setNotification] = useState(null)
  const [filterStatus, setFilterStatus] = useState('All')

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 3500)
  }

  // 1. Fetch Projects on mount
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch(`${API_BASE}/projects`, { headers })
        if (res.ok) {
          const data = await res.json()
          setProjects(data)
          if (data.length > 0 && !selectedProjectId) {
            setSelectedProjectId(data[0].id)
          }
        }
      } catch (err) {
        console.warn('Projects API unavailable:', err)
      }
    }
    fetchProjects()
  }, [token])

  // 2. Fetch Scope Items whenever selectedProjectId changes
  useEffect(() => {
    if (!selectedProjectId) {
      setScopeItems([])
      setSelectedScopeItemId('')
      return
    }
    const fetchScopeItems = async () => {
      try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch(`${API_BASE}/scope-items?project_id=${selectedProjectId}`, { headers })
        if (res.ok) {
          const data = await res.json()
          setScopeItems(data)
          if (data.length > 0) {
            setSelectedScopeItemId(data[0].id)
          } else {
            setSelectedScopeItemId('')
          }
        }
      } catch (err) {
        console.warn('Scope items API error:', err)
      }
    }
    fetchScopeItems()
  }, [selectedProjectId, token])

  // 3. Fetch Tasks
  const fetchTasks = async () => {
    setLoading(true)
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const res = await fetch(`${API_BASE}/tasks`, { headers })
      if (res.ok) {
        const data = await res.json()
        setTasks(data)
      }
    } catch (err) {
      console.warn('Tasks API error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [token])

  // Save Task (Create or Edit)
  const handleSaveTask = async (e) => {
    e.preventDefault()
    if (!taskTitle.trim()) {
      showNotification('Task title is required.', 'error')
      return
    }
    if (!selectedProjectId) {
      showNotification('Please select a project.', 'error')
      return
    }
    if (!selectedScopeItemId) {
      showNotification('Please link this task to a scope item deliverable.', 'error')
      return
    }

    setLoading(true)
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }

      if (editingId) {
        // PUT update
        const payload = {
          project_id: selectedProjectId,
          scope_item_id: selectedScopeItemId,
          title: taskTitle.trim(),
          due_date: dueDate || null,
          status: taskStatus,
        }
        const res = await fetch(`${API_BASE}/tasks/${editingId}`, {
          method: 'PUT',
          headers,
          body: JSON.stringify(payload),
        })
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.detail || 'Failed to update task')
        }
        const updated = await res.json()
        setTasks((prev) => prev.map((t) => (t.id === editingId ? updated : t)))
        showNotification('Task updated successfully!')
        handleCancelEdit()
      } else {
        // POST create
        const payload = {
          project_id: selectedProjectId,
          scope_item_id: selectedScopeItemId,
          title: taskTitle.trim(),
          due_date: dueDate || null,
          status: taskStatus,
        }
        const res = await fetch(`${API_BASE}/tasks`, {
          method: 'POST',
          headers,
          body: JSON.stringify(payload),
        })
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.detail || 'Failed to create task')
        }
        const created = await res.json()
        setTasks((prev) => [created, ...prev])
        showNotification('Task created and linked to scope deliverable!')
        setTaskTitle('')
        setDueDate('')
        setTaskStatus('To do')
      }
    } catch (err) {
      showNotification(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  // Quick Status Change directly from Task List
  const handleQuickStatusChange = async (taskId, newStatus) => {
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ status: newStatus }),
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to update status')
      }
      const updated = await res.json()
      setTasks((prev) => prev.map((t) => (t.id === taskId ? updated : t)))
      showNotification(`Task status updated to "${newStatus}"`)
    } catch (err) {
      showNotification(err.message, 'error')
    }
  }

  // Delete Task
  const handleDeleteTask = async (taskId) => {
    if (!confirm('Are you sure you want to delete this task?')) return
    setLoading(true)
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
        method: 'DELETE',
        headers,
      })
      if (!res.ok) {
        throw new Error('Failed to delete task')
      }
      setTasks((prev) => prev.filter((t) => t.id !== taskId))
      showNotification('Task deleted.')
      if (editingId === taskId) handleCancelEdit()
    } catch (err) {
      showNotification(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleEditTask = (task) => {
    setEditingId(task.id)
    setSelectedProjectId(task.project_id)
    setSelectedScopeItemId(task.scope_item_id)
    setTaskTitle(task.title)
    setDueDate(task.due_date || '')
    setTaskStatus(task.status)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setTaskTitle('')
    setDueDate('')
    setTaskStatus('To do')
  }

  // Filter tasks by status if selected
  const filteredTasks = tasks.filter((t) => {
    if (filterStatus === 'All') return true
    return t.status === filterStatus
  })

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
          <button onClick={() => setNotification(null)} className="text-xs opacity-70 hover:opacity-100">
            ✕
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 mb-2">
            Scope-Linked Task Execution
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Task Management</h2>
          <p className="text-sm text-slate-400 mt-1">
            Every task is contractually tied to an approved Scope of Work deliverable.
          </p>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          {['All', 'To do', 'Doing', 'Done'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                filterStatus === st ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Task Creation / Edit Form */}
      <form onSubmit={handleSaveTask} className="mt-8 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
            {editingId ? 'Edit Task' : 'Add New Scope Task'}
          </h3>
          <span className="text-xs text-slate-400">Strict Project & Scope Consistency Enforced</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Project Selection Dropdown */}
          <div>
            <label className="text-xs uppercase font-bold text-slate-400 mb-1.5 block">Project</label>
            <select
              value={selectedProjectId}
              onChange={(e) => {
                setSelectedProjectId(e.target.value)
              }}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              {projects.length === 0 ? (
                <option value="">No projects available</option>
              ) : (
                projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.status})
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Scope Item Selection Dropdown */}
          <div>
            <label className="text-xs uppercase font-bold text-slate-400 mb-1.5 block">
              Related Scope Item
            </label>
            <select
              value={selectedScopeItemId}
              onChange={(e) => setSelectedScopeItemId(e.target.value)}
              disabled={scopeItems.length === 0}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none disabled:opacity-40"
            >
              {scopeItems.length === 0 ? (
                <option value="">No scope items for this project</option>
              ) : (
                scopeItems.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.included_description.slice(0, 75)}...
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Task Title Input */}
          <div className="md:col-span-2">
            <label className="text-xs uppercase font-bold text-slate-400 mb-1.5 block">Task Title</label>
            <input
              type="text"
              value={taskTitle}
              onChange={(e) => setTaskTitle(e.target.value)}
              placeholder="e.g. Implement responsive navigation bar and mobile drawer"
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          {/* Due Date Picker */}
          <div>
            <label className="text-xs uppercase font-bold text-slate-400 mb-1.5 block">Due Date</label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          {/* Task Status Dropdown */}
          <div>
            <label className="text-xs uppercase font-bold text-slate-400 mb-1.5 block">Status</label>
            <select
              value={taskStatus}
              onChange={(e) => setTaskStatus(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl p-2.5 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            >
              <option value="To do">To do</option>
              <option value="Doing">Doing</option>
              <option value="Done">Done</option>
            </select>
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
            disabled={loading || scopeItems.length === 0}
            className="px-6 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl shadow-lg shadow-indigo-500/30 transition disabled:opacity-50"
          >
            {loading ? 'Processing...' : editingId ? 'Update Task' : 'Add Task'}
          </button>
        </div>
      </form>

      {/* Task Listing */}
      <div className="mt-12">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            Task Backlog & Progress
            <span className="text-xs font-normal px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400">
              {filteredTasks.length} tasks
            </span>
          </h3>
          <button
            onClick={fetchTasks}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition"
          >
            ↻ Refresh List
          </button>
        </div>

        {filteredTasks.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
            <p className="text-slate-400 text-sm">No tasks found matching current filter.</p>
            <p className="text-xs text-slate-500 mt-1">Select a project with scope items above to create your first task.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Task Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {task.project_name || 'Project'}
                    </span>
                    <h4 className="text-base font-semibold text-white truncate">{task.title}</h4>
                  </div>
                  <p className="text-xs text-slate-400 truncate">
                    <strong className="text-slate-300">Scope Deliverable:</strong>{' '}
                    {task.scope_item_summary || 'Linked SOW Deliverable'}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                    <span>
                      Due:{' '}
                      <strong className={task.due_date ? 'text-slate-300' : 'text-slate-500 italic'}>
                        {task.due_date || 'No due date'}
                      </strong>
                    </span>
                    <span>&bull;</span>
                    <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {/* Status & Actions */}
                <div className="flex items-center gap-3 shrink-0">
                  {/* Status Dropdown: Allows quick status change directly from list */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-slate-400">Status:</span>
                    <select
                      value={task.status}
                      onChange={(e) => handleQuickStatusChange(task.id, e.target.value)}
                      className={`text-xs font-semibold rounded-lg px-2.5 py-1 border focus:outline-none cursor-pointer transition ${
                        task.status === 'Done'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : task.status === 'Doing'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                      }`}
                    >
                      <option value="To do" className="bg-slate-900 text-slate-200">
                        To do
                      </option>
                      <option value="Doing" className="bg-slate-900 text-slate-200">
                        Doing
                      </option>
                      <option value="Done" className="bg-slate-900 text-slate-200">
                        Done
                      </option>
                    </select>
                  </div>

                  {/* Edit Button */}
                  <button
                    onClick={() => handleEditTask(task)}
                    className="px-3 py-1 text-xs font-medium text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-md border border-indigo-500/30 transition"
                  >
                    Edit
                  </button>

                  {/* Delete Button */}
                  <button
                    onClick={() => handleDeleteTask(task.id)}
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
  )
}
