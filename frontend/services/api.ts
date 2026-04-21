import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000, // 2 minutes for LLM calls
});

// Request interceptor: attach auth token
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem('research-ide-auth');
      if (stored) {
        const parsed = JSON.parse(stored);
        const token = parsed?.state?.accessToken;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
    } catch {}
  }
  return config;
});

// Response interceptor: handle 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      try {
        const stored = localStorage.getItem('research-ide-auth');
        if (stored) {
          const parsed = JSON.parse(stored);
          const refreshToken = parsed?.state?.refreshToken;
          if (refreshToken) {
            const resp = await axios.post(`${API_URL}/api/auth/refresh`, {
              refresh_token: refreshToken,
            });
            const newToken = resp.data.access_token;
            // Update stored token
            parsed.state.accessToken = newToken;
            localStorage.setItem('research-ide-auth', JSON.stringify(parsed));
            // Retry original request
            error.config.headers.Authorization = `Bearer ${newToken}`;
            return api.request(error.config);
          }
        }
      } catch {}
      // Refresh failed — clear auth
      localStorage.removeItem('research-ide-auth');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data: { email: string; password: string; name: string; skill_level?: string }) =>
    api.post('/auth/register', data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data).then((r) => r.data),

  me: () => api.get('/auth/me').then((r) => r.data),

  updateMe: (data: Partial<{ name: string; skill_level: string; interests: string[] }>) =>
    api.patch('/auth/me', data).then((r) => r.data),
};

// ── Projects ──────────────────────────────────────────────────────────────────
export const projectsAPI = {
  list: () => api.get('/projects/').then((r) => r.data),

  create: (data: { title: string; input_text: string }) =>
    api.post('/projects/', data).then((r) => r.data),

  get: (id: string) => api.get(`/projects/${id}`).then((r) => r.data),

  updateStage: (id: string, stage: string) =>
    api.patch(`/projects/${id}/stage`, { stage }).then((r) => r.data),

  delete: (id: string) => api.delete(`/projects/${id}`).then((r) => r.data),
};

// ── Pipeline ──────────────────────────────────────────────────────────────────
export const pipelineAPI = {
  extractIntent: (projectId: string, text?: string) =>
    api.post('/pipeline/intent', { project_id: projectId, text }).then((r) => r.data),

  retrievePapers: (projectId: string, maxPapers = 20) =>
    api.post('/pipeline/retrieve', { project_id: projectId, max_papers: maxPapers }).then((r) => r.data),
};

// ── Agents ───────────────────────────────────────────────────────────────────
export const agentsAPI = {
  analyzeGaps: (projectId: string) =>
    api.post('/agents/analyze-gaps', { project_id: projectId }).then((r) => r.data),

  generateIdeas: (projectId: string) =>
    api.post('/agents/generate-ideas', { project_id: projectId }).then((r) => r.data),

  selectIdea: (projectId: string, ideaIndex: number) =>
    api.post('/agents/select-idea', { project_id: projectId, idea_index: ideaIndex }).then((r) => r.data),

  createPlan: (projectId: string) =>
    api.post('/agents/plan', { project_id: projectId }).then((r) => r.data),

  generateCode: (projectId: string) =>
    api.post('/agents/generate-code', { project_id: projectId }).then((r) => r.data),

  generateReport: (projectId: string) =>
    api.post('/agents/generate-report', { project_id: projectId }).then((r) => r.data),
};

// ── LLM Config ───────────────────────────────────────────────────────────────
export const llmAPI = {
  listProviders: () => api.get('/llm/providers').then((r) => r.data),

  getOllamaModels: (baseUrl?: string) =>
    api.get('/llm/ollama/models', { params: { base_url: baseUrl } }).then((r) => r.data),

  saveApiKey: (provider: string, apiKey: string) =>
    api.post('/llm/keys', { provider, api_key: apiKey }).then((r) => r.data),

  deleteApiKey: (provider: string) =>
    api.delete(`/llm/keys/${provider}`).then((r) => r.data),

  getKeysStatus: () => api.get('/llm/keys/status').then((r) => r.data),

  setPreferences: (provider: string, model: string, ollamaBaseUrl?: string) =>
    api
      .post('/llm/preferences', { provider, model, ollama_base_url: ollamaBaseUrl })
      .then((r) => r.data),

  testConnection: (data: { provider: string; model?: string; api_key?: string; ollama_base_url?: string }) =>
    api.post('/llm/test', data).then((r) => r.data),
};

export default api;
