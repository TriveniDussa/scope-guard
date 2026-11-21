import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/v1'

export default function RequestChecker({ token }) {
  const [projects, setProjects] = useState([
    { id: '11111111-1111-1111-1111-111111111111', name: 'Website Redesign', status: 'Active' },
    { id: '22222222-2222-2222-2222-222222222222', name: 'Mobile App Refresh', status: 'Active' },
  ])
  const [selectedProjectId, setSelectedProjectId] = useState('11111111-1111-1111-1111-111111111111')
  const [clientRequestText, setClientRequestText] = useState('')
  const [evaluating, setEvaluating] = useState(false)
  const [evaluationResult, setEvaluationResult] = useState(null)
  const [history, setHistory] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [notification, setNotification] = useState(null)
  const [copied, setCopied] = useState(false)
  const [filterProjectId, setFilterProjectId] = useState('All')

  // Day 9: Feedback and Check Again state
  const [feedbackMode, setFeedbackMode] = useState(null) // null | 'Right' | 'Wrong'
  const [correctResult, setCorrectResult] = useState('In scope')
  const [correctionReason, setCorrectionReason] = useState('')
  const [submittingFeedback, setSubmittingFeedback] = useState(false)
  const [checkingAgain, setCheckingAgain] = useState(false)
  const [checkAgainComparison, setCheckAgainComparison] = useState(null) // { old_answer, new_answer }

  // Lessons list state
  const [lessons, setLessons] = useState([])
  const [viewTab, setViewTab] = useState('history') // 'history' | 'lessons'

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type })
    setTimeout(() => setNotification(null), 4000)
  }

  // 1. Fetch Projects from backend
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch(`${API_BASE}/projects`, { headers })
        if (res.ok) {
          const data = await res.json()
          if (data && data.length > 0) {
            setProjects(data)
            if (!selectedProjectId) {
              setSelectedProjectId(data[0].id)
            }
          }
        }
      } catch (err) {
        console.warn('Projects API unavailable:', err)
      }
    }
    fetchProjects()
  }, [token])

  // 2. Fetch Request History from backend
  const fetchHistory = async () => {
    setLoadingHistory(true)
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const url =
        filterProjectId !== 'All'
          ? `${API_BASE}/requests?project_id=${filterProjectId}`
          : `${API_BASE}/requests`
      const res = await fetch(url, { headers })
      if (res.ok) {
        const data = await res.json()
        setHistory(data)
      }
    } catch (err) {
      console.warn('Requests history API error:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // 3. Fetch Lessons Learned from backend
  const fetchLessons = async () => {
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const url =
        filterProjectId !== 'All'
          ? `${API_BASE}/lessons?project_id=${filterProjectId}`
          : `${API_BASE}/lessons`
      const res = await fetch(url, { headers })
      if (res.ok) {
        const data = await res.json()
        setLessons(data)
      }
    } catch (err) {
      console.warn('Lessons API error:', err)
    }
  }

  useEffect(() => {
    fetchHistory()
    fetchLessons()
  }, [token, filterProjectId])

  // 4. Handle Submit Request Check
  const handleCheckRequest = async (e) => {
    e.preventDefault()
    if (!clientRequestText.trim()) {
      showNotification('Please enter the client request description.', 'error')
      return
    }
    if (!selectedProjectId) {
      showNotification('Please select a project.', 'error')
      return
    }

    setEvaluating(true)
    setEvaluationResult(null)
    setCheckAgainComparison(null)
    setFeedbackMode(null)

    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }
      const res = await fetch(`${API_BASE}/requests/check`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          project_id: selectedProjectId,
          client_request: clientRequestText.trim(),
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setEvaluationResult(data)
        showNotification(`Request classified as: ${data.classification}`, 'success')
        fetchHistory()
        fetchLessons()
      } else {
        const errorData = await res.json().catch(() => ({}))
        const detailMsg = errorData.detail || 'Evaluation failed. Check backend configuration.'
        showNotification(detailMsg, 'error')
      }
    } catch (err) {
      console.warn('Check request failed:', err)
      showNotification('Backend connection failed. Please ensure FastAPI server is running.', 'error')
    } finally {
      setEvaluating(false)
    }
  }

  // 5. Handle Feedback (Right / Wrong)
  const handleRightFeedback = async (requestId) => {
    setSubmittingFeedback(true)
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }
      const res = await fetch(`${API_BASE}/requests/${requestId}/feedback`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ feedback: 'Right' }),
      })

      if (res.ok) {
        const updated = await res.json()
        setEvaluationResult(updated)
        setFeedbackMode(null)
        showNotification('Feedback saved: Confirmed correct by agency.', 'success')
        fetchHistory()
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Failed to submit feedback.', 'error')
      }
    } catch (err) {
      showNotification('Error saving feedback.', 'error')
    } finally {
      setSubmittingFeedback(false)
    }
  }

  const handleWrongFeedbackSubmit = async (e, requestId) => {
    e.preventDefault()
    if (!correctionReason.trim()) {
      showNotification('Please provide a one-line correction reason.', 'error')
      return
    }

    setSubmittingFeedback(true)
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }
      const res = await fetch(`${API_BASE}/requests/${requestId}/feedback`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          feedback: 'Wrong',
          correct_result: correctResult,
          correction_reason: correctionReason.trim(),
        }),
      })

      if (res.ok) {
        const updated = await res.json()
        setEvaluationResult(updated)
        setFeedbackMode(null)
        setCorrectionReason('')
        showNotification(
          `Correction lesson saved! AI will now use this guidance for future checks.`,
          'success'
        )
        fetchHistory()
        fetchLessons()
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Failed to submit correction.', 'error')
      }
    } catch (err) {
      showNotification('Error saving correction lesson.', 'error')
    } finally {
      setSubmittingFeedback(false)
    }
  }

  // 6. Handle Check Again
  const handleCheckAgain = async (requestId) => {
    if (!requestId) return
    setCheckingAgain(true)
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      }
      const res = await fetch(`${API_BASE}/requests/${requestId}/check-again`, {
        method: 'POST',
        headers,
      })

      if (res.ok) {
        const data = await res.json()
        setCheckAgainComparison(data)
        setEvaluationResult(data.new_answer)
        setFeedbackMode(null)
        showNotification('Request re-evaluated with current scope & lessons!', 'success')
        fetchHistory()
        fetchLessons()
      } else {
        const err = await res.json().catch(() => ({}))
        showNotification(err.detail || 'Check Again failed.', 'error')
      }
    } catch (err) {
      showNotification('Error connecting to backend for Check Again.', 'error')
    } finally {
      setCheckingAgain(false)
    }
  }

  // Copy reply to clipboard
  const handleCopyReply = (textToCopy) => {
    if (!textToCopy) return
    navigator.clipboard.writeText(textToCopy)
    setCopied(true)
    showNotification('Polite client reply copied to clipboard!', 'success')
    setTimeout(() => setCopied(false), 2500)
  }

  // Styling helpers
  const getBadgeStyle = (classification) => {
    switch (classification) {
      case 'In scope':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
      case 'Out of scope':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30'
      case 'Not sure':
      default:
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30'
    }
  }

  const getBorderAccent = (classification) => {
    switch (classification) {
      case 'In scope':
        return 'border-l-emerald-500'
      case 'Out of scope':
        return 'border-l-rose-500'
      case 'Not sure':
      default:
        return 'border-l-amber-500'
    }
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

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs text-indigo-400 font-semibold mb-2">
            <span>✨</span> Day 9: Learning Functionality & Check Again
          </div>
          <h2 className="text-3xl font-extrabold text-white tracking-tight">
            Scope Creep <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Guardian</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Evaluate requests against scope deliverables and fine-tune AI decisions through agency correction lessons.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            AI Engine: <strong className="text-white">Gemini 1.5 Flash + Lessons</strong>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Input Form (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span>
              Evaluate Client Request
            </h3>

            <form onSubmit={handleCheckRequest} className="space-y-4">
              {/* Project Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Select Project
                </label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                  required
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.status || 'Active'})
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-500 mt-1">
                  AI reads only this project's scope items and saved correction lessons.
                </p>
              </div>

              {/* Client Request Textarea */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Client's New Request
                </label>
                <textarea
                  rows={6}
                  value={clientRequestText}
                  onChange={(e) => setClientRequestText(e.target.value)}
                  placeholder="e.g. Can you add a multi-currency payment gateway and checkout in Hindi?"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition resize-none leading-relaxed"
                  required
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={evaluating || !clientRequestText.trim()}
                className="w-full py-3 px-4 rounded-xl text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-600/30 transition flex items-center justify-center gap-2"
              >
                {evaluating ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                    </svg>
                    <span>Evaluating Against Scope & Lessons...</span>
                  </>
                ) : (
                  <>
                    <span>✨ Check Request</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Quick Guidance Box */}
          <div className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-4 text-xs text-slate-400 space-y-2">
            <p className="font-semibold text-slate-300 flex items-center gap-1.5">
              <span>🧠</span> Continuous Learning Architecture:
            </p>
            <ul className="list-disc list-inside space-y-1 text-slate-400 pl-1">
              <li><strong className="text-slate-300">Human-in-the-Loop:</strong> Rate answers Right or Wrong to teach the system.</li>
              <li><strong className="text-slate-300">Hierarchy of Truth:</strong> Scope baseline is primary; lessons provide guidance.</li>
              <li><strong className="text-slate-300">Check Again:</strong> Re-evaluates requests after scope updates or correction lessons.</li>
              <li><strong className="text-slate-300">Strict Immutability:</strong> Original answers are preserved; comparisons are transparent.</li>
            </ul>
          </div>
        </div>

        {/* Right Column: AI Analysis Result, Feedback, Check Again, and Backlog (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Check Again Comparison Display (Old Answer vs New Answer) */}
          {checkAgainComparison && (
            <div className="p-6 rounded-2xl bg-indigo-950/30 border border-indigo-800/50 shadow-2xl backdrop-blur animate-fadeIn">
              <div className="flex items-center justify-between mb-4 border-b border-indigo-800/40 pb-3">
                <span className="text-xs uppercase tracking-wider text-indigo-400 font-bold flex items-center gap-1.5">
                  <span>🔄</span> Check Again: Comparison View
                </span>
                <span className="text-xs text-slate-400">
                  Original preserved &bull; New evaluation recorded
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* OLD ANSWER */}
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      OLD ANSWER
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getBadgeStyle(checkAgainComparison.old_answer.classification)}`}>
                      {checkAgainComparison.old_answer.classification}
                    </span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div>
                      <strong className="text-slate-400 block mb-0.5">Reason:</strong>
                      <p className="text-slate-300 bg-slate-900/50 p-2 rounded border border-slate-800/60 leading-relaxed">
                        {checkAgainComparison.old_answer.reason}
                      </p>
                    </div>
                    <div>
                      <strong className="text-slate-400 block mb-0.5">Client Reply:</strong>
                      <p className="text-slate-400 italic bg-slate-900/50 p-2 rounded border border-slate-800/60">
                        "{checkAgainComparison.old_answer.client_reply}"
                      </p>
                    </div>
                  </div>
                </div>

                {/* NEW ANSWER */}
                <div className={`p-4 rounded-xl bg-slate-950/80 border border-slate-800 border-l-4 ${getBorderAccent(checkAgainComparison.new_answer.classification)}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                      <span>✨</span> NEW ANSWER
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getBadgeStyle(checkAgainComparison.new_answer.classification)}`}>
                      {checkAgainComparison.new_answer.classification}
                    </span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div>
                      <strong className="text-slate-400 block mb-0.5">Reason:</strong>
                      <p className="text-slate-200 bg-slate-900/50 p-2 rounded border border-slate-800/60 leading-relaxed">
                        {checkAgainComparison.new_answer.reason}
                      </p>
                    </div>
                    <div>
                      <div className="flex items-center justify-between mb-0.5">
                        <strong className="text-indigo-400">Client Reply:</strong>
                        <button
                          onClick={() => handleCopyReply(checkAgainComparison.new_answer.client_reply)}
                          className="text-[11px] text-indigo-400 hover:text-indigo-300"
                        >
                          📋 Copy
                        </button>
                      </div>
                      <p className="text-indigo-200 bg-indigo-950/20 p-2 rounded border border-indigo-900/40 leading-relaxed">
                        {checkAgainComparison.new_answer.client_reply}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Active AI Decision Card */}
          {evaluationResult && (
            <div className={`p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur border-l-4 ${getBorderAccent(evaluationResult.classification)} animate-fadeIn`}>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                  AI Decision Card {evaluationResult.parent_request_id && <span className="text-indigo-400 font-normal">(Re-evaluation)</span>}
                </span>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${getBadgeStyle(
                      evaluationResult.classification
                    )}`}
                  >
                    {evaluationResult.classification}
                  </span>
                  {/* Check Again Button */}
                  <button
                    onClick={() => handleCheckAgain(evaluationResult.id)}
                    disabled={checkingAgain}
                    className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 transition flex items-center gap-1.5 disabled:opacity-50"
                    title="Re-evaluate this request with latest scope and learned lessons"
                  >
                    {checkingAgain ? (
                      <>
                        <svg className="animate-spin h-3.5 w-3.5 text-indigo-300" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                        </svg>
                        <span>Re-evaluating...</span>
                      </>
                    ) : (
                      <>
                        <span>🔄 Check Again</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Client Request Quote */}
              <div className="mb-4 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80">
                <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block mb-1">
                  Evaluated Request:
                </span>
                <p className="text-sm text-slate-200 italic">"{evaluationResult.client_request}"</p>
              </div>

              {/* AI Justification / Reason */}
              <div className="mb-4">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block mb-1">
                  Why this classification?
                </span>
                <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/40 p-3 rounded-xl border border-slate-800/60">
                  {evaluationResult.reason}
                </p>
              </div>

              {/* Drafted Polite Reply */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[11px] uppercase tracking-wider text-indigo-400 font-semibold">
                    Client Reply Draft:
                  </span>
                  <button
                    onClick={() => handleCopyReply(evaluationResult.client_reply)}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
                  >
                    <span>{copied ? '✓ Copied' : '📋 Copy Draft'}</span>
                  </button>
                </div>
                <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-900/40 text-sm text-indigo-200 leading-relaxed">
                  {evaluationResult.client_reply}
                </div>
              </div>

              {/* FEEDBACK SECTION */}
              <div className="border-t border-slate-800 pt-4">
                {evaluationResult.feedback ? (
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-slate-400 font-medium">Agency Feedback:</span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full font-bold border ${
                        evaluationResult.feedback === 'Right'
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {evaluationResult.feedback === 'Right' ? '✓ Marked Right' : '✕ Corrected as Wrong (Lesson Stored)'}
                    </span>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-slate-300">
                        Was this answer correct?
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleRightFeedback(evaluationResult.id)}
                          disabled={submittingFeedback}
                          className="px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30 transition disabled:opacity-50"
                        >
                          ✓ Right
                        </button>
                        <button
                          onClick={() => setFeedbackMode(feedbackMode === 'Wrong' ? null : 'Wrong')}
                          disabled={submittingFeedback}
                          className={`px-3 py-1 rounded-lg text-xs font-semibold transition border ${
                            feedbackMode === 'Wrong'
                              ? 'bg-rose-600 text-white border-rose-500'
                              : 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border-rose-500/30'
                          }`}
                        >
                          ✕ Wrong
                        </button>
                      </div>
                    </div>

                    {/* Expandable Wrong Correction Form */}
                    {feedbackMode === 'Wrong' && (
                      <form
                        onSubmit={(e) => handleWrongFeedbackSubmit(e, evaluationResult.id)}
                        className="mt-3 p-4 rounded-xl bg-slate-950 border border-rose-900/40 space-y-3 animate-fadeIn"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-rose-400">
                            Correction Details for Lessons Knowledge Base
                          </span>
                        </div>

                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                            Correct Result:
                          </label>
                          <select
                            value={correctResult}
                            onChange={(e) => setCorrectResult(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
                          >
                            <option value="In scope">In scope</option>
                            <option value="Out of scope">Out of scope</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                            One-line Correction Reason:
                          </label>
                          <input
                            type="text"
                            value={correctionReason}
                            onChange={(e) => setCorrectionReason(e.target.value)}
                            placeholder="e.g. The contact form is explicitly included in the agreed scope."
                            className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-rose-500"
                            required
                          />
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => setFeedbackMode(null)}
                            className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={submittingFeedback || !correctionReason.trim()}
                            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition disabled:opacity-50"
                          >
                            {submittingFeedback ? 'Saving Lesson...' : 'Save Lesson'}
                          </button>
                        </div>
                      </form>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tabbed Backlog: Request History vs Lessons Learned */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              {/* Tab selector */}
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
                <button
                  onClick={() => setViewTab('history')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                    viewTab === 'history'
                      ? 'bg-indigo-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  📜 Request History ({history.length})
                </button>
                <button
                  onClick={() => setViewTab('lessons')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                    viewTab === 'lessons'
                      ? 'bg-indigo-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  🧠 Lessons Learned ({lessons.length})
                </button>
              </div>

              {/* Project filter */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Project:</span>
                <select
                  value={filterProjectId}
                  onChange={(e) => setFilterProjectId(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none"
                >
                  <option value="All">All Projects</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => {
                    fetchHistory()
                    fetchLessons()
                  }}
                  disabled={loadingHistory}
                  className="p-1 text-slate-400 hover:text-slate-200 transition"
                  title="Refresh"
                >
                  ↻
                </button>
              </div>
            </div>

            {/* View Tab 1: Request History */}
            {viewTab === 'history' && (
              <div>
                {loadingHistory ? (
                  <div className="py-8 text-center text-xs text-slate-500">Loading history...</div>
                ) : history.length === 0 ? (
                  <div className="py-12 text-center border border-dashed border-slate-800 rounded-xl">
                    <p className="text-sm text-slate-400">No requests evaluated yet.</p>
                    <p className="text-xs text-slate-500 mt-1">Submit your first client request on the left to check scope.</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                    {history.map((item) => (
                      <div
                        key={item.id}
                        className={`p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition border-l-4 ${getBorderAccent(
                          item.classification
                        )}`}
                      >
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-xs font-semibold text-slate-300">
                            {item.project_name || 'Project'}{' '}
                            {item.parent_request_id && (
                              <span className="text-[10px] text-indigo-400 font-normal">
                                (Re-evaluation)
                              </span>
                            )}
                          </span>
                          <div className="flex items-center gap-1.5">
                            {item.feedback && (
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  item.feedback === 'Right'
                                    ? 'bg-emerald-500/10 text-emerald-400'
                                    : 'bg-rose-500/10 text-rose-400'
                                }`}
                              >
                                {item.feedback === 'Right' ? '✓ Right' : '✕ Corrected'}
                              </span>
                            )}
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-bold border ${getBadgeStyle(
                                item.classification
                              )}`}
                            >
                              {item.classification}
                            </span>
                          </div>
                        </div>

                        <p className="text-sm text-slate-200 mb-2 font-medium">"{item.client_request}"</p>

                        <p className="text-xs text-slate-400 mb-3 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                          <strong className="text-slate-300">Reason:</strong> {item.reason}
                        </p>

                        <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-800/60">
                          <span>{new Date(item.created_at).toLocaleString()}</span>
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => {
                                setEvaluationResult(item)
                                setCheckAgainComparison(null)
                                setFeedbackMode(null)
                              }}
                              className="text-slate-300 hover:text-white transition text-[11px]"
                            >
                              Inspect / Feedback
                            </button>
                            <button
                              onClick={() => handleCheckAgain(item.id)}
                              disabled={checkingAgain}
                              className="text-indigo-400 hover:text-indigo-300 transition text-[11px] font-medium"
                            >
                              🔄 Check Again
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* View Tab 2: Lessons Learned */}
            {viewTab === 'lessons' && (
              <div>
                {lessons.length === 0 ? (
                  <div className="py-12 text-center border border-dashed border-slate-800 rounded-xl">
                    <p className="text-sm text-slate-400">No lessons recorded yet.</p>
                    <p className="text-xs text-slate-500 mt-1">
                      When the AI produces a Wrong result, provide a correction to record an agency lesson here.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                    {lessons.map((lesson) => (
                      <div
                        key={lesson.id}
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition border-l-4 border-l-amber-500"
                      >
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <span className="text-xs font-semibold text-slate-300">
                            {lesson.project_name || 'Project'}
                          </span>
                          <div className="flex items-center gap-1.5 text-xs">
                            <span className="text-slate-500">AI: {lesson.ai_answer} &rarr;</span>
                            <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${getBadgeStyle(lesson.correct_result)}`}>
                              Correct: {lesson.correct_result}
                            </span>
                          </div>
                        </div>

                        <p className="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/60">
                          <strong className="text-amber-400">Correction Reason:</strong> {lesson.correction_reason}
                        </p>

                        <div className="text-[11px] text-slate-500 mt-2">
                          Recorded: {new Date(lesson.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
