using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using StudentEngagementSystem.Models;
using StudentEngagementSystem.Repositories.Interfaces;
using StudentEngagementSystem.Services.Interfaces;
using StudentEngagementSystem.ViewModels.Videos;
using System.Security.Claims;
using System.Text.Json;

namespace StudentEngagementSystem.Controllers
{
    [Authorize]
    public class VideosController : Controller
    {
        private readonly IVideoRepository _videoRepository;
        private readonly IStudentRepository _studentRepository;
        private readonly IAnalysisResultRepository _analysisResultRepository;
        private readonly IAIAnalysisService _aiAnalysisService;
        private readonly IWebHostEnvironment _webHostEnvironment;

        public VideosController(
            IVideoRepository videoRepository,
            IStudentRepository studentRepository,
            IAnalysisResultRepository analysisResultRepository,
            IAIAnalysisService aiAnalysisService,
            IWebHostEnvironment webHostEnvironment)
        {
            _videoRepository = videoRepository;
            _studentRepository = studentRepository;
            _analysisResultRepository = analysisResultRepository;
            _aiAnalysisService = aiAnalysisService;
            _webHostEnvironment = webHostEnvironment;
        }

        [HttpGet]
        public async Task<IActionResult> Upload(int studentId)
        {
            var student = await _studentRepository.GetByIdAsync(studentId, GetTeacherId());
            if (student == null) return NotFound();

            var model = new VideoUploadViewModel
            {
                StudentId = student.StudentId,
                StudentName = student.FullName
            };
            return View(model);
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        [RequestSizeLimit(524288000)] // 500MB
        public async Task<IActionResult> Upload(VideoUploadViewModel model)
        {
            var student = await _studentRepository.GetByIdAsync(model.StudentId, GetTeacherId());
            if (student == null) return NotFound();
            model.StudentName = student.FullName;

            if (ModelState.IsValid)
            {
                if (model.VideoFile == null || model.VideoFile.Length == 0)
                {
                    ModelState.AddModelError("VideoFile", "Please select a valid video file.");
                    return View(model);
                }

                var extension = Path.GetExtension(model.VideoFile.FileName).ToLowerInvariant();
                var allowedExtensions = new[] { ".mp4", ".avi", ".mov" };
                if (!allowedExtensions.Contains(extension))
                {
                    ModelState.AddModelError("VideoFile", "Only MP4, AVI, and MOV files are allowed.");
                    return View(model);
                }

                // 1. Save video locally
                string uploadsFolder = Path.Combine(_webHostEnvironment.WebRootPath, "uploads", "videos");
                Directory.CreateDirectory(uploadsFolder);
                string uniqueFileName = Guid.NewGuid().ToString() + extension;
                string filePath = Path.Combine(uploadsFolder, uniqueFileName);

                using (var stream = new FileStream(filePath, FileMode.Create))
                {
                    await model.VideoFile.CopyToAsync(stream);
                }

                // 2. Save video info to SQL Server
                var video = new Video
                {
                    StudentId = model.StudentId,
                    VideoName = model.VideoName,
                    VideoPath = uniqueFileName,
                    UploadDate = DateTime.UtcNow
                };
                await _videoRepository.AddAsync(video);

                // 3. Send to FastAPI
                var analysisDto = await _aiAnalysisService.AnalyzeVideoAsync(filePath);

                if (analysisDto != null)
                {
                    // 6. Save returned analysis
                    var result = new AnalysisResult
                    {
                        VideoId = video.VideoId,
                        EngagementPercentage = analysisDto.EngagementPercentage,
                        FocusedPercentage = analysisDto.FocusedPercentage,
                        DistractedPercentage = analysisDto.DistractedPercentage,
                        DominantEmotion = analysisDto.DominantEmotion,
                        EmotionNeutral = analysisDto.EmotionDistribution.Neutral,
                        EmotionHappy = analysisDto.EmotionDistribution.Happy,
                        EmotionSad = analysisDto.EmotionDistribution.Sad,
                        EmotionAngry = analysisDto.EmotionDistribution.Angry,
                        EmotionFear = analysisDto.EmotionDistribution.Fearful,
                        EmotionDisgust = analysisDto.EmotionDistribution.Disgusted,
                        EmotionSurprised = analysisDto.EmotionDistribution.Surprised,
                        DisengagementIntervals = JsonSerializer.Serialize(analysisDto.DisengagementIntervals),
                        EngagementTimeline = JsonSerializer.Serialize(analysisDto.EngagementTimeline),
                        EmotionTimeline = JsonSerializer.Serialize(analysisDto.EmotionTimeline)
                    };
                    await _analysisResultRepository.AddAsync(result);

                    // --- Notifications Logic ---
                    var dbContext = HttpContext.RequestServices.GetService(typeof(StudentEngagementSystem.Data.ApplicationDbContext)) as StudentEngagementSystem.Data.ApplicationDbContext;
                    if (dbContext != null)
                    {
                        var teacherId = GetTeacherId();
                        var analysisUrl = Url.Action("Details", "Analysis", new { videoId = video.VideoId });
                        
                        // Success Notification
                        dbContext.Notifications.Add(new Notification
                        {
                            TeacherId = teacherId,
                            Title = "Analysis Complete",
                            Message = $"The video '{video.VideoName}' for {student.FullName} has been analyzed.",
                            Type = "Success",
                            LinkUrl = analysisUrl,
                            CreatedAt = DateTime.UtcNow
                        });

                        // Warning Notification if low engagement
                        if (analysisDto.EngagementPercentage < 50)
                        {
                            dbContext.Notifications.Add(new Notification
                            {
                                TeacherId = teacherId,
                                Title = "Low Engagement Alert",
                                Message = $"Warning: {student.FullName} showed only {analysisDto.EngagementPercentage}% engagement in '{video.VideoName}'.",
                                Type = "Warning",
                                LinkUrl = analysisUrl,
                                CreatedAt = DateTime.UtcNow
                            });
                        }
                        await dbContext.SaveChangesAsync();
                    }
                    // --- End Notifications Logic ---

                    TempData["SuccessMessage"] = "Video uploaded and analyzed successfully.";
                    // 7. Redirect to Analysis page
                    return RedirectToAction("Details", "Analysis", new { videoId = video.VideoId });
                }
                else
                {
                    TempData["ErrorMessage"] = "Video uploaded but AI Analysis failed. Please try analyzing later.";
                    return RedirectToAction("Details", "Students", new { id = model.StudentId });
                }
            }
            return View(model);
        }

        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var video = await _videoRepository.GetByIdAsync(id, GetTeacherId());
            if (video != null)
            {
                var studentId = video.StudentId;
                string filePath = Path.Combine(_webHostEnvironment.WebRootPath, "uploads", "videos", video.VideoPath);
                if (System.IO.File.Exists(filePath))
                {
                    System.IO.File.Delete(filePath);
                }
                await _videoRepository.DeleteAsync(video);
                TempData["SuccessMessage"] = "Video deleted successfully.";
                return RedirectToAction("Details", "Students", new { id = studentId });
            }
            return NotFound();
        }

        public async Task<IActionResult> Download(int id)
        {
            var video = await _videoRepository.GetByIdAsync(id, GetTeacherId());
            if (video == null) return NotFound();

            string filePath = Path.Combine(_webHostEnvironment.WebRootPath, "uploads", "videos", video.VideoPath);
            if (!System.IO.File.Exists(filePath)) return NotFound();

            byte[] fileBytes = await System.IO.File.ReadAllBytesAsync(filePath);
            return File(fileBytes, "application/octet-stream", video.VideoName + Path.GetExtension(video.VideoPath));
        }

        private string GetTeacherId()
        {
            return User.FindFirstValue(ClaimTypes.NameIdentifier)!;
        }
    }
}
