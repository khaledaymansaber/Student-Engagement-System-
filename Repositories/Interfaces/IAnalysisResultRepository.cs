using StudentEngagementSystem.Models;

namespace StudentEngagementSystem.Repositories.Interfaces
{
    public interface IAnalysisResultRepository
    {
        Task<AnalysisResult?> GetByVideoIdAsync(int videoId, string teacherId);
        Task AddAsync(AnalysisResult analysisResult);
    }
}
