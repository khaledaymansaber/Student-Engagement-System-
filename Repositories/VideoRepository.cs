using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Data;
using StudentEngagementSystem.Models;
using StudentEngagementSystem.Repositories.Interfaces;

namespace StudentEngagementSystem.Repositories
{
    public class VideoRepository : IVideoRepository
    {
        private readonly ApplicationDbContext _context;

        public VideoRepository(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<IEnumerable<Video>> GetAllByStudentIdAsync(int studentId, string teacherId)
        {
            return await _context.Videos
                .Include(v => v.Student)
                .Where(v => v.StudentId == studentId && v.Student!.TeacherId == teacherId)
                .OrderByDescending(v => v.UploadDate)
                .ToListAsync();
        }

        public async Task<Video?> GetByIdAsync(int id, string teacherId)
        {
            return await _context.Videos
                .Include(v => v.Student)
                .FirstOrDefaultAsync(v => v.VideoId == id && v.Student!.TeacherId == teacherId);
        }

        public async Task<Video?> GetByIdWithAnalysisAsync(int id, string teacherId)
        {
            return await _context.Videos
                .Include(v => v.Student)
                .Include(v => v.AnalysisResult)
                .FirstOrDefaultAsync(v => v.VideoId == id && v.Student!.TeacherId == teacherId);
        }

        public async Task AddAsync(Video video)
        {
            await _context.Videos.AddAsync(video);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(Video video)
        {
            _context.Videos.Remove(video);
            await _context.SaveChangesAsync();
        }

        public async Task<int> GetCountByTeacherIdAsync(string teacherId)
        {
            return await _context.Videos
                .CountAsync(v => v.Student!.TeacherId == teacherId);
        }

        public async Task<int> GetAnalyzedCountByTeacherIdAsync(string teacherId)
        {
            return await _context.Videos
                .CountAsync(v => v.Student!.TeacherId == teacherId && v.AnalysisResult != null);
        }

        public async Task<IEnumerable<Video>> GetRecentByTeacherIdAsync(string teacherId, int count)
        {
            return await _context.Videos
                .Include(v => v.Student)
                .Include(v => v.AnalysisResult)
                .Where(v => v.Student!.TeacherId == teacherId)
                .OrderByDescending(v => v.UploadDate)
                .Take(count)
                .ToListAsync();
        }
    }
}
