using System.ComponentModel.DataAnnotations;

namespace StudentEngagementSystem.ViewModels.Students
{
    public class StudentCreateViewModel
    {
        [Required]
        [Display(Name = "Full Name")]
        [StringLength(100)]
        public string FullName { get; set; } = string.Empty;

        [Required]
        [Display(Name = "Student ID / Code")]
        [StringLength(50)]
        public string StudentCode { get; set; } = string.Empty;

        [Display(Name = "Student Photo (Optional)")]
        public IFormFile? PhotoFile { get; set; }
    }

    public class StudentEditViewModel : StudentCreateViewModel
    {
        public int StudentId { get; set; }
        public string? ExistingPhotoPath { get; set; }
    }

    public class StudentDetailsViewModel
    {
        public int StudentId { get; set; }
        public string FullName { get; set; } = string.Empty;
        public string StudentCode { get; set; } = string.Empty;
        public string? Photo { get; set; }
        public DateTime CreatedDate { get; set; }
        public IEnumerable<Models.Video> Videos { get; set; } = new List<Models.Video>();
    }
}
