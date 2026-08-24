export function getRecommendedJobs(jobs, resumeSkills) {
  return jobs
    .map((job) => {
      const matchingSkills = job.skills.filter((skill) =>
        resumeSkills.includes(skill)
      )

      return {
        ...job,
        matchingSkills,
        matchCount: matchingSkills.length,
        matchScore: Math.round((matchingSkills.length / job.skills.length) * 100),
      }
    })
    .filter((job) => job.matchCount > 0)
    .sort((a, b) => b.matchCount - a.matchCount)
}