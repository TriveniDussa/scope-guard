import React, { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Clients() {
  const { authFetch } = useAuth()
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)
  const [notification, setNotification] = useState(null)

  // Form state
  const [clientName, setClientName] = useState('')
  const [clientEmail, setClientEmail] = useState('')
  const [editingClient, setEditingClient] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 3500)
  }

  // Fetch all clients
  const fetchClients = async () => {
    setLoading(true)
    try {
      const res = await authFetch('/clients')
      if (res.ok) {
        const data = await res.json()
        setClients(data)
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Failed to load clients', 'error')
      }
    } catch (err) {
      console.warn('Clients API fetch error:', err)
      showNotification('Could not connect to clients service', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchClients()
  }, [])

  // Create or Update Client
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!clientName.trim()) {
      showNotification('Client name is required', 'error')
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        name: clientName.trim(),
        email: clientEmail.trim() || null,
      }

      if (editingClient) {
        // PUT update
        const res = await authFetch(`/clients/${editingClient.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (res.ok) {
          showNotification('Client updated successfully')
          setEditingClient(null)
          setClientName('')
          setClientEmail('')
          fetchClients()
        } else {
          const err = await res.json().catch(() => ({}))
          showNotification(err.detail || 'Failed to update client', 'error')
        }
      } else {
        // POST create
        const res = await authFetch('/clients', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })

        if (res.ok) {
          showNotification('Client added successfully')
          setClientName('')
          setClientEmail('')
          fetchClients()
        } else {
          const err = await res.json().catch(() => ({}))
          showNotification(err.detail || 'Failed to create client', 'error')
        }
      }
    } catch (err) {
      showNotification('Network error while saving client', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  // Edit action
  const handleEdit = (client) => {
    setEditingClient(client)
    setClientName(client.name)
    setClientEmail(client.email || '')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelEdit = () => {
    setEditingClient(null)
    setClientName('')
    setClientEmail('')
  }

  // Delete action
  const handleDelete = async (clientId, clientTitle) => {
    if (!window.confirm(`Are you sure you want to delete client "${clientTitle}"? All associated projects and scope baselines will be permanently deleted.`)) {
      return
    }

    try {
      const res = await authFetch(`/clients/${clientId}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        showNotification(`Client "${clientTitle}" deleted`)
        if (editingClient?.id === clientId) {
          handleCancelEdit()
        }
        fetchClients()
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Failed to delete client', 'error')
      }
    } catch (err) {
      showNotification('Network error while deleting client', 'error')
    }
  }

  const filteredClients = clients.filter(
    (c) =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.email && c.email.toLowerCase().includes(searchTerm.toLowerCase()))
  )

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
            <span>🏢</span> Client Directory
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            Client <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Management</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Manage your agency client accounts, contact details, and engagements.
          </p>
        </div>

        <div className="text-xs text-slate-400 bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 flex items-center gap-2 self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
          <span>Total Clients: <strong className="text-white">{clients.length}</strong></span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Create / Edit Form (5 cols) */}
        <div className="lg:col-span-5">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur sticky top-24">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${editingClient ? 'bg-amber-400' : 'bg-indigo-500'}`}></span>
              {editingClient ? 'Edit Client Account' : 'Add New Client'}
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Client Organization / Name *
                </label>
                <input
                  type="text"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Primary Contact Email (Optional)
                </label>
                <input
                  type="email"
                  value={clientEmail}
                  onChange={(e) => setClientEmail(e.target.value)}
                  placeholder="e.g. contact@acme.com"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                {editingClient && (
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
                  disabled={submitting || !clientName.trim()}
                  className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold text-white transition disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex items-center justify-center gap-2 ${
                    editingClient
                      ? 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/30'
                      : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-600/30'
                  }`}
                >
                  {submitting ? (
                    <span>Saving...</span>
                  ) : editingClient ? (
                    <span>Update Client</span>
                  ) : (
                    <span>+ Add Client</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Client Listing (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Search bar */}
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search clients by name or email..."
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <span className="absolute left-3 top-2.5 text-slate-500 text-xs">🔍</span>
            </div>
            <button
              onClick={fetchClients}
              className="text-xs text-indigo-400 hover:text-indigo-300 transition shrink-0"
            >
              ↻ Refresh
            </button>
          </div>

          {/* List */}
          {loading ? (
            <div className="py-16 text-center text-xs text-slate-500">Loading client directory...</div>
          ) : filteredClients.length === 0 ? (
            <div className="py-16 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/30">
              <p className="text-slate-400 text-sm">No clients found.</p>
              <p className="text-xs text-slate-500 mt-1">Add your first agency client using the form on the left.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredClients.map((client) => (
                <div
                  key={client.id}
                  className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <h4 className="text-base font-semibold text-white truncate">{client.name}</h4>
                    <p className="text-xs text-slate-400 truncate mt-0.5">
                      {client.email ? (
                        <span className="flex items-center gap-1.5">
                          <span>✉️</span> {client.email}
                        </span>
                      ) : (
                        <span className="italic text-slate-600">No contact email provided</span>
                      )}
                    </p>
                    <span className="text-[11px] text-slate-500 block mt-1.5">
                      Added: {new Date(client.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <button
                      onClick={() => handleEdit(client)}
                      className="px-3 py-1 text-xs font-medium text-indigo-400 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-md border border-indigo-500/30 transition"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(client.id, client.name)}
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
