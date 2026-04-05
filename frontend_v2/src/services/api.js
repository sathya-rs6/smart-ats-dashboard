import axios from 'axios';

// Empty baseURL lets Vite's proxy forward requests to http://localhost:8000
const apiClient = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const api = {
  // Auth
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 form requires username
    formData.append('password', password);
    return apiClient.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).then(res => res.data);
  },
  register: (name, email, password, appPassword) =>
    apiClient.post('/auth/register', {
      name, email, password, smtp_app_password: appPassword
    }).then(res => res.data),

  // Dashboard & Jobs
  getDashboardStats: () => apiClient.get('/dashboard/stats').then(res => res.data),
  createJob: (jobData) => apiClient.post('/job-descriptions/', jobData).then(res => res.data),
  getJobs: () => apiClient.get('/jobs/').then(res => res.data),

  // Resumes
  getResumes: () => apiClient.get('/resumes/').then(res => res.data),
  bulkUploadResumes: (files, onUploadProgress) => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f.file));
    
    return apiClient.post('/resumes/bulk-upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }).then(res => res.data);
  },
  
  // Rankings & Analysis History
  getRankings: (jobId) => apiClient.get(`/jobs/${jobId}/rankings`).then(res => res.data),
  getTopResumes: () => apiClient.get('/resumes/top/').then(res => res.data),
  getAnalyses: () => apiClient.get('/analyses/').then(res => res.data),
  
  // RAG Chatbot
  // Assumes a chat endpoint exists or uses a standard analysis prompt
  askAssistant: (resumeId, question) => apiClient.post('/chat/', {
    resume_id: resumeId,
    query: question,
  }).then(res => res.data),

  // Email Notification
  // Assumes an endpoint exists for sending shortlist emails
  sendShortlistEmail: (candidateId, jobId) => {
    const smtpPassword = localStorage.getItem('smtp_app_password');
    const smtpEmail = localStorage.getItem('smtp_email');
    return apiClient.post('/notifications/shortlist', {
      candidate_id: candidateId,
      job_id: jobId,
      smtp_app_password: smtpPassword || undefined,
      smtp_email: smtpEmail || undefined
    }).then(res => res.data);
  }
};
