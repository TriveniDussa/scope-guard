// Centralized API configuration reading environment variables with fallback
const rawBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
export const API_BASE = rawBase.replace(/\/+$/, '')

