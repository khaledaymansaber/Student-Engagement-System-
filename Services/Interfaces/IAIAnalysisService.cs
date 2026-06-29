using StudentEngagementSystem.DTOs;

namespace StudentEngagementSystem.Services.Interfaces
{
    public interface IAIAnalysisService
    {
        Task<FastApiResponseDto?> AnalyzeVideoAsync(string videoPath);
        Task<bool> IsServiceAvailableAsync();
    }
}
