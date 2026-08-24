import './App.css'
import { useEffect, useState } from 'react'
import {
  analyzeResume,
  askAssistant,
  getFilterOptions,
  getJobs,
  getRecommendations,
} from './services/jobsService'

const assistantSuggestions = [
  'Which jobs should I apply for?',
  'What skills am I missing?',
  'How should I prepare for this role?',
]

function App() {

  const [selectedSource, setSelectedSource] = useState('all')
  const [skillSearch, setSkillSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedExperience, setSelectedExperience] = useState('all')
  const [resumeFileName, setResumeFileName] = useState('')
  const [resumeSkills, setResumeSkills] = useState([])
  const [resumeStatus, setResumeStatus] = useState('')
  const [isAnalyzingResume, setIsAnalyzingResume] = useState(false)
  const [recommendedJobs, setRecommendedJobs] = useState([])
  const [geminiApiKey, setGeminiApiKey] = useState('')
  const [assistantQuestion, setAssistantQuestion] = useState('')
  const [assistantResponse, setAssistantResponse] = useState('')
  const [isAskingAssistant, setIsAskingAssistant] = useState(false)

  const [jobs, setJobs] = useState([])
  const [totalJobs, setTotalJobs] = useState(0)
  const [offset, setOffset] = useState(0)
  const [filterOptions, setFilterOptions] = useState({
    sources: [],
    categories: [],
    experience_levels: [],
  })
  const [isLoadingJobs, setIsLoadingJobs] = useState(true)
  const [jobsError, setJobsError] = useState('')

  const clearFilters = () => {
    setSelectedSource('all')
    setSkillSearch('')
    setSelectedCategory('all')
    setSelectedExperience('all')
    setOffset(0)
  }

  const handleResumeUpload = async (event) => {
    const file = event.target.files[0]

    if (!file) {
      setResumeFileName('')
      setResumeSkills([])
      setRecommendedJobs([])
      return
    }

    setResumeFileName(file.name)
    setResumeStatus('Analyzing resume...')
    setIsAnalyzingResume(true)

    try {
      const analysis = await analyzeResume(file)
      setResumeSkills(analysis.profile.skills)
      const recommendations = analysis.profile.skills.length
        ? await getRecommendations(analysis.profile)
        : { items: [] }
      setRecommendedJobs(recommendations.items)
      setResumeStatus(
        analysis.profile.skills.length > 0
          ? `Found skills: ${analysis.profile.skills.join(', ')}${
              analysis.profile.roles.length
                ? `. Detected role: ${analysis.profile.roles[0]}`
                : ''
            }${
              analysis.profile.detected_experience
                ? `. Experience: ${analysis.profile.detected_experience}`
                : ''
            }`
          : 'No matching skills were found in the current job database.'
      )
    } catch (error) {
      setResumeSkills([])
      setRecommendedJobs([])
      setResumeStatus(error.message)
    } finally {
      setIsAnalyzingResume(false)
    }
  }

  const handleAskAssistant = async () => {
    if (!assistantQuestion.trim() || !geminiApiKey.trim()) {
      setAssistantResponse('Enter both your Gemini API key and a question.')
      return
    }

    setIsAskingAssistant(true)
    setAssistantResponse('')

    try {
      const response = await askAssistant({
        apiKey: geminiApiKey,
        question: assistantQuestion,
        resumeSkills,
        jobIds: jobs.map((job) => job.id),
      })
      setAssistantResponse(response.answer)
    } catch (error) {
      setAssistantResponse(error.message)
    } finally {
      setIsAskingAssistant(false)
    }
  }

  useEffect(() => {
    const loadJobs = async () => {
      setIsLoadingJobs(true)
      setJobsError('')
      try {
        const jobsData = await getJobs({
          source: selectedSource,
          skill: skillSearch,
          category: selectedCategory,
          experience: selectedExperience,
        }, offset)
        setJobs(jobsData.items)
        setTotalJobs(jobsData.total)
      } catch (error) {
        setJobsError(error.message)
      } finally {
        setIsLoadingJobs(false)
      }
    }

    loadJobs()
  }, [selectedSource, skillSearch, selectedCategory, selectedExperience, offset])

  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        setFilterOptions(await getFilterOptions())
      } catch (error) {
        setJobsError(error.message)
      }
    }

    loadFilterOptions()
  }, [])

  return (
    <main className="app">
      <section className="hero">
        <h1>AI-Powered Job Board</h1>
        <p>Find, filter, and understand jobs with AI assistance.</p>
      </section>


      <section className="dashboard">
        <aside className="filters-panel">
          <h2>Filters</h2>

          <p className="jobs-summary">Matching jobs: {totalJobs}</p>

          <label htmlFor="source">Job Source</label>
          <select id="source" name="source" value={selectedSource}
            onChange={(event) => {
              setSelectedSource(event.target.value)
              setOffset(0)
            }}>
            <option value="all">All Platforms</option>
            {filterOptions.sources.map((source) => (
              <option value={source} key={source}>{source}</option>
            ))}
          </select>

          <label htmlFor="skill">Skill</label>
          <input
            id="skill"
            name="skill"
            type="text"
            placeholder="Search Python, SQL, React..."
            value={skillSearch}
            onChange={(event) => {
              setSkillSearch(event.target.value)
              setOffset(0)
            }}
          />
          <label htmlFor="category">Role Category</label>
          <select
            id="category"
            name="category"
            value={selectedCategory}
            onChange={(event) => {
              setSelectedCategory(event.target.value)
              setOffset(0)
            }}
          >
            <option value="all">All Categories</option>
            {filterOptions.categories.map((category) => (
              <option value={category} key={category}>{category}</option>
            ))}
          </select>

          <label htmlFor="experience">Experience</label>
          <select
            id="experience"
            name="experience"
            value={selectedExperience}
            onChange={(event) => {
              setSelectedExperience(event.target.value)
              setOffset(0)
            }}
          >
            <option value="all">All Experience Levels</option>
            {filterOptions.experience_levels.map((experience) => (
              <option value={experience} key={experience}>{experience}</option>
            ))}
          </select>

          <button className="clear-filters-button" type="button" onClick={clearFilters}>
            Clear Filters
          </button>



        </aside>



        <section className="jobs-panel">

          <section className="recommendations-panel">
            <h2>Recommended for You</h2>
            <p>Upload your resume to prepare personalized job matches.</p>

            <label className="resume-upload">
              <span>Upload Resume</span>
              <input
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleResumeUpload}
              />
            </label>

            {resumeFileName && (
              <p className="selected-resume">
                Selected file: {resumeFileName}. {resumeStatus}
              </p>
            )}
            {isAnalyzingResume && <p className="selected-resume">Please wait...</p>}
            {recommendedJobs.length > 0 && (
              <div className="recommended-list">
                {recommendedJobs.map((job) => (
                  <article className="recommended-card" key={job.id}>
                    <h3>{job.title}</h3>
                    <p>{job.company}</p>
                    <strong>{job.recommendation_score}% recommendation score</strong>
                    <span>
                      Skill coverage: {job.skill_coverage}% | Matched skills: {job.matching_skills.join(', ')}
                    </span>
                  </article>
                ))}
              </div>
            )}
          </section>

          <h2>Available Jobs ({totalJobs})</h2>

          {isLoadingJobs && <p className="empty-state">Loading jobs...</p>}
          {jobsError && <p className="empty-state">{jobsError}</p>}

          {!isLoadingJobs && !jobsError && (
            <>
              <div className="job-list">
                {jobs.length === 0 ? (
                  <p className="empty-state">No jobs found for these filters.</p>
                ) : (
                  jobs.map((job) => (
                    <article className="job-card" key={job.id}>
                      <div>
                        <h3>{job.title}</h3>
                        <span className="job-id">Job ID: {job.id}</span>
                        <p>{job.company} • {job.location} • {job.experience}</p>
                      </div>

                      <span className="job-source">{job.source}</span>
                      <span className="job-category">{job.category}</span>
                      {job.domain && job.domain !== 'Not specified' && (
                        <span className="job-domain">{job.domain}</span>
                      )}
                      {job.is_ai_enriched && (
                        <span className="ai-enriched-badge">AI enriched</span>
                      )}
                      <p className="job-description">{job.description}</p>

                      <div className="skill-list">
                        {job.skills.map((skill) => (
                          <span className="skill-tag" key={skill}>
                            {skill}
                          </span>
                        ))}
                      </div>
                      {job.is_ai_enriched && (
                        <details className="original-tags">
                          <summary>View original dataset tags</summary>
                          <p>Category: {job.raw_category}</p>
                          <p>Experience: {job.raw_experience}</p>
                          <p>Skills: {job.raw_skills.join(', ')}</p>
                        </details>
                      )}
                    </article>
                  ))
                )}
              </div>
              {jobs.length > 0 && (
                <div className="pagination-controls">
                  <button
                    type="button"
                    onClick={() => setOffset(Math.max(0, offset - 20))}
                    disabled={offset === 0}
                  >
                    Previous
                  </button>
                  <span>Page {Math.floor(offset / 20) + 1}</span>
                  <button
                    type="button"
                    onClick={() => setOffset(offset + 20)}
                    disabled={offset + jobs.length >= totalJobs}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </section>

        <section className="assistant-panel">
          <h2>AI Job Assistant</h2>
          <p>Ask questions about jobs, skills, preparation, and career fit.</p>
          <div className="suggestion-list">
            {assistantSuggestions.map((suggestion) => (
              <button
                className="suggestion-button"
                type="button"
                key={suggestion}
                onClick={() => setAssistantQuestion(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>

          <label htmlFor="apiKey">Gemini API Key</label>
          <input
            id="apiKey"
            name="apiKey"
            type="password"
            placeholder="Enter your Gemini API key"
            value={geminiApiKey}
            onChange={(event) => setGeminiApiKey(event.target.value)}
          />

          <label htmlFor="assistantQuestion">Your Question</label>
          <textarea
            id="assistantQuestion"
            name="assistantQuestion"
            rows="5"
            placeholder="Example: Which jobs should I apply for?"
            value={assistantQuestion}
            onChange={(event) => setAssistantQuestion(event.target.value)}
          />

          <button
            className="ask-button"
            type="button"
            onClick={handleAskAssistant}
            disabled={!assistantQuestion.trim() || !geminiApiKey.trim() || isAskingAssistant}
          >
            {isAskingAssistant ? 'Thinking...' : 'Ask Assistant'}
          </button>

          <div className="assistant-response">
            <p>
              {assistantResponse || 'Enter your Gemini API key and ask a question.'}
            </p>
          </div>
        </section>
      </section>
    </main>
  )
}

export default App
