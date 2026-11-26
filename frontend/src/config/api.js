// // Centralized API configuration reading environment variables with fallback
// const rawBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
// export const API_BASE = rawBase.replace(/\/+$/, '')


// Centralized API configuration
const rawBase =
  import.meta.env.VITE_API_BASE_URL ||
  'https://scope-guard-backend.onrender.com/api/v1';

export const API_BASE = rawBase.replace(/\/+$/, '');
