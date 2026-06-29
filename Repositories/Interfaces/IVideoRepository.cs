using StudentEngagementSystem.Models;

namespace StudentEngagementSystem.Repositories.Interfaces
{
    public interface IVideoRepository
    {
        Task<IEnumerable<Video>> GetAllByStudentIdAsync(int studentId, string teacherId);
        Task<Video?> GetByIdAsync(int id, string teacherId);
        Task<Video?> GetByIdWithAnalysisAsync(int id, string teacherId);
        Task AddAsync(Video video);
        Task DeleteAsync(Video video);
        Task<int> GetCountByTeacherIdAsync(string teacherId);
        Task<int> GetAnalyzedCountByTeacherIdAsync(string teacherId);
        Task<IEnumerable<Video>> GetRecentByTeacherIdAsync(string teacherId, int count);
    }
}
