const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Something went wrong while contacting the API.')
  }

  return response.json()
}

export function getJobs(filters, offset) {
  const parameters = new URLSearchParams({ limit: '20', offset: String(offset) })

  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== 'all') {
      parameters.set(key, value)
    }
  })

  return request(`/jobs?${parameters.toString()}`)
}

export function getFilterOptions() {
  return request('/filters')
}

export function analyzeResume(file) {
  const formData = new FormData()
  formData.append('file', file)

  return request('/resumes/analyze', {
    method: 'POST',
    body: formData,
  })
}

export function getRecommendations(resumeProfile) {
  return request('/recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume_skills: resumeProfile.skills,
      resume_roles: resumeProfile.roles,
      experience_years: resumeProfile.experience_years,
      limit: 10,
    }),
  })
}

export function askAssistant({ apiKey, question, resumeSkills, jobIds }) {
  return request('/assistant/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: apiKey,
      question,
      resume_skills: resumeSkills,
      job_ids: jobIds,
    }),
  })
}
