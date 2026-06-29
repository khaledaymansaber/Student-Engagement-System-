using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using StudentEngagementSystem.Models;
using StudentEngagementSystem.Repositories.Interfaces;
using StudentEngagementSystem.ViewModels.Students;
using System.Security.Claims;

namespace StudentEngagementSystem.Controllers
{
    [Authorize]
    public class StudentsController : Controller
    {
        private readonly IStudentRepository _studentRepository;
        private readonly IWebHostEnvironment _webHostEnvironment;

        public StudentsController(IStudentRepository studentRepository, IWebHostEnvironment webHostEnvironment)
        {
            _studentRepository = studentRepository;
            _webHostEnvironment = webHostEnvironment;
        }

        public async Task<IActionResult> Index()
        {
            var teacherId = GetTeacherId();
            var students = await _studentRepository.GetAllByTeacherIdAsync(teacherId);
            return View(students);
        }

        public IActionResult Create()
        {
            return View(new StudentCreateViewModel());
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Create(StudentCreateViewModel model)
        {
            if (ModelState.IsValid)
            {
                string? uniqueFileName = await ProcessUploadedFile(model.PhotoFile);
                var student = new Student
                {
                    FullName = model.FullName,
                    StudentCode = model.StudentCode,
                    TeacherId = GetTeacherId(),
                    Photo = uniqueFileName
                };

                await _studentRepository.AddAsync(student);
                TempData["SuccessMessage"] = "Student added successfully.";
                return RedirectToAction(nameof(Index));
            }
            return View(model);
        }

        public async Task<IActionResult> Details(int id)
        {
            var student = await _studentRepository.GetByIdWithVideosAsync(id, GetTeacherId());
            if (student == null) return NotFound();

            var model = new StudentDetailsViewModel
            {
                StudentId = student.StudentId,
                FullName = student.FullName,
                StudentCode = student.StudentCode,
                Photo = student.Photo,
                CreatedDate = student.CreatedDate,
                Videos = student.Videos.OrderByDescending(v => v.UploadDate)
            };
            return View(model);
        }

        public async Task<IActionResult> Edit(int id)
        {
            var student = await _studentRepository.GetByIdAsync(id, GetTeacherId());
            if (student == null) return NotFound();

            var model = new StudentEditViewModel
            {
                StudentId = student.StudentId,
                FullName = student.FullName,
                StudentCode = student.StudentCode,
                ExistingPhotoPath = student.Photo
            };
            return View(model);
        }

        [HttpPost]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> Edit(int id, StudentEditViewModel model)
        {
            if (id != model.StudentId) return BadRequest();

            if (ModelState.IsValid)
            {
                var student = await _studentRepository.GetByIdAsync(id, GetTeacherId());
                if (student == null) return NotFound();

                student.FullName = model.FullName;
                student.StudentCode = model.StudentCode;

                if (model.PhotoFile != null)
                {
                    // If a new photo is uploaded, delete the old one if it exists
                    if (student.Photo != null)
                    {
                        string filePath = Path.Combine(_webHostEnvironment.WebRootPath, "uploads", "photos", student.Photo);
                        if (System.IO.File.Exists(filePath))
                        {
                            System.IO.File.Delete(filePath);
                        }
                    }
                    student.Photo = await ProcessUploadedFile(model.PhotoFile);
                }

                await _studentRepository.UpdateAsync(student);
                TempData["SuccessMessage"] = "Student updated successfully.";
                return RedirectToAction(nameof(Index));
            }
            return View(model);
        }

        [HttpPost, ActionName("Delete")]
        [ValidateAntiForgeryToken]
        public async Task<IActionResult> DeleteConfirmed(int id)
        {
            var student = await _studentRepository.GetByIdAsync(id, GetTeacherId());
            if (student != null)
            {
                // Delete photo
                if (student.Photo != null)
                {
                    string filePath = Path.Combine(_webHostEnvironment.WebRootPath, "uploads", "photos", student.Photo);
                    if (System.IO.File.Exists(filePath))
                    {
                        System.IO.File.Delete(filePath);
                    }
                }
                await _studentRepository.DeleteAsync(student);
                TempData["SuccessMessage"] = "Student deleted successfully.";
            }
            return RedirectToAction(nameof(Index));
        }

        private string GetTeacherId()
        {
            return User.FindFirstValue(ClaimTypes.NameIdentifier)!;
        }

        private async Task<string?> ProcessUploadedFile(IFormFile? photoFile)
        {
            string? uniqueFileName = null;

            if (photoFile != null)
            {
                string uploadsFolder = Path.Combine(_webHostEnvironment.WebRootPath, "uploads", "photos");
                Directory.CreateDirectory(uploadsFolder);
                
                uniqueFileName = Guid.NewGuid().ToString() + "_" + photoFile.FileName;
                string filePath = Path.Combine(uploadsFolder, uniqueFileName);
                using (var fileStream = new FileStream(filePath, FileMode.Create))
                {
                    await photoFile.CopyToAsync(fileStream);
                }
            }
            return uniqueFileName;
        }
    }
}
