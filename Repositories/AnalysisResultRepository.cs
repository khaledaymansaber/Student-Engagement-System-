using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Data;
using StudentEngagementSystem.Models;
using StudentEngagementSystem.Repositories.Interfaces;

namespace StudentEngagementSystem.Repositories
{
    public class AnalysisResultRepository : IAnalysisResultRepository
    {
        private readonly ApplicationDbContext _context;

        public AnalysisResultRepository(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<AnalysisResult?> GetByVideoIdAsync(int videoId, string teacherId)
        {
            return await _context.AnalysisResults
                .Include(a => a.Video)
                    .ThenInclude(v => v!.Student)
                .FirstOrDefaultAsync(a => a.VideoId == videoId && a.Video!.Student!.TeacherId == teacherId);
        }

        public async Task AddAsync(AnalysisResult analysisResult)
        {
            await _context.AnalysisResults.AddAsync(analysisResult);
            await _context.SaveChangesAsync();
        }
    }
}
