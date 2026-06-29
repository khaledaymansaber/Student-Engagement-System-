using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using StudentEngagementSystem.Repositories.Interfaces;
using StudentEngagementSystem.ViewModels.Dashboard;
using System.Security.Claims;

namespace StudentEngagementSystem.Controllers
{
    [Authorize]
    public class DashboardController : Controller
    {
        private readonly IStudentRepository _studentRepository;
        private readonly IVideoRepository _videoRepository;

        public DashboardController(IStudentRepository studentRepository, IVideoRepository videoRepository)
        {
            _studentRepository = studentRepository;
            _videoRepository = videoRepository;
        }

        public async Task<IActionResult> Index()
        {
            var teacherId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            if (string.IsNullOrEmpty(teacherId))
            {
                return RedirectToAction("Login", "Account");
            }

            var model = new DashboardViewModel
            {
                TotalStudents = await _studentRepository.GetCountByTeacherIdAsync(teacherId),
                TotalVideos = await _videoRepository.GetCountByTeacherIdAsync(teacherId),
                AnalyzedVideos = await _videoRepository.GetAnalyzedCountByTeacherIdAsync(teacherId),
                RecentStudents = await _studentRepository.GetAllByTeacherIdAsync(teacherId), // Taking all for now, can limit in repo later
                RecentVideos = await _videoRepository.GetRecentByTeacherIdAsync(teacherId, 5)
            };

            // Limit recent students to 5
            model.RecentStudents = model.RecentStudents.Take(5);

            return View(model);
        }
    }
}
