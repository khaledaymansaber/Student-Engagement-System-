using StudentEngagementSystem.Models;

namespace StudentEngagementSystem.Repositories.Interfaces
{
    public interface IStudentRepository
    {
        Task<IEnumerable<Student>> GetAllByTeacherIdAsync(string teacherId);
        Task<Student?> GetByIdAsync(int id, string teacherId);
        Task<Student?> GetByIdWithVideosAsync(int id, string teacherId);
        Task AddAsync(Student student);
        Task UpdateAsync(Student student);
        Task DeleteAsync(Student student);
        Task<int> GetCountByTeacherIdAsync(string teacherId);
    }
}
