using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Data;
using StudentEngagementSystem.Models;
using StudentEngagementSystem.Repositories.Interfaces;

namespace StudentEngagementSystem.Repositories
{
    public class StudentRepository : IStudentRepository
    {
        private readonly ApplicationDbContext _context;

        public StudentRepository(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<IEnumerable<Student>> GetAllByTeacherIdAsync(string teacherId)
        {
            return await _context.Students
                .Where(s => s.TeacherId == teacherId)
                .OrderByDescending(s => s.CreatedDate)
                .ToListAsync();
        }

        public async Task<Student?> GetByIdAsync(int id, string teacherId)
        {
            return await _context.Students
                .FirstOrDefaultAsync(s => s.StudentId == id && s.TeacherId == teacherId);
        }

        public async Task<Student?> GetByIdWithVideosAsync(int id, string teacherId)
        {
            return await _context.Students
                .Include(s => s.Videos)
                    .ThenInclude(v => v.AnalysisResult)
                .FirstOrDefaultAsync(s => s.StudentId == id && s.TeacherId == teacherId);
        }

        public async Task AddAsync(Student student)
        {
            await _context.Students.AddAsync(student);
            await _context.SaveChangesAsync();
        }

        public async Task UpdateAsync(Student student)
        {
            _context.Students.Update(student);
            await _context.SaveChangesAsync();
        }

        public async Task DeleteAsync(Student student)
        {
            _context.Students.Remove(student);
            await _context.SaveChangesAsync();
        }

        public async Task<int> GetCountByTeacherIdAsync(string teacherId)
        {
            return await _context.Students.CountAsync(s => s.TeacherId == teacherId);
        }
    }
}
