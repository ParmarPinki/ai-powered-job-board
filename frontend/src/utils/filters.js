export function filterJobs(jobs, filters) {
  const searchText = filters.skillSearch.trim().toLowerCase()

  return jobs.filter((job) => {
    const matchesSource =
      filters.selectedSource === 'all' ||
      job.source.toLowerCase() === filters.selectedSource

    const matchesSkill =
      searchText === '' ||
      job.skills.some((skill) => skill.toLowerCase() === searchText)

    const matchesCategory =
      filters.selectedCategory === 'all' ||
      job.category === filters.selectedCategory

    const matchesExperience =
      filters.selectedExperience === 'all' ||
      job.experience === filters.selectedExperience

    return matchesSource && matchesSkill && matchesCategory && matchesExperience
  })
}