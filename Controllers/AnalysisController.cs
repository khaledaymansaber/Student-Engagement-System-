using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using StudentEngagementSystem.Repositories.Interfaces;
using StudentEngagementSystem.ViewModels.Analysis;
using System.Security.Claims;
using System.Threading.Tasks;
using System.Linq;

namespace StudentEngagementSystem.Controllers
{
    [Authorize]
    public class AnalysisController : Controller
    {
        private readonly IVideoRepository _videoRepository;
        private readonly IStudentRepository _studentRepository;

        public AnalysisController(IVideoRepository videoRepository, IStudentRepository studentRepository)
        {
            _videoRepository = videoRepository;
            _studentRepository = studentRepository;
        }

        public async Task<IActionResult> Details(int videoId)
        {
            var teacherId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            if (string.IsNullOrEmpty(teacherId)) return Challenge();

            var video = await _videoRepository.GetByIdWithAnalysisAsync(videoId, teacherId);
            
            if (video == null) return NotFound("Video not found or access denied.");
            if (video.AnalysisResult == null) return NotFound("Analysis result not found for this video.");
            if (video.Student == null) return NotFound("Student not found.");

            var allStudents = await _studentRepository.GetAllByTeacherIdAsync(teacherId);

            var model = new AnalysisViewModel
            {
                Video = video,
                AnalysisResult = video.AnalysisResult,
                Student = video.Student,
                StudentsList = allStudents.ToList(),
                EngagementTimelineJson = video.AnalysisResult.EngagementTimeline,
                EmotionTimelineJson = video.AnalysisResult.EmotionTimeline,
                DisengagementIntervalsJson = video.AnalysisResult.DisengagementIntervals
            };

            return View(model);
        }
    }
}
