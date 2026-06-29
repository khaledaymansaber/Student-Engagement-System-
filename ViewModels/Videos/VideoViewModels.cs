using System.ComponentModel.DataAnnotations;
using Microsoft.AspNetCore.Http;

namespace StudentEngagementSystem.ViewModels.Videos
{
    public class VideoUploadViewModel
    {
        [Required]
        public int StudentId { get; set; }

        public string StudentName { get; set; } = string.Empty;

        [Required(ErrorMessage = "Please select a video file.")]
        [Display(Name = "Video File")]
        public IFormFile? VideoFile { get; set; }

        [Required]
        [StringLength(255)]
        [Display(Name = "Video Title / Name")]
        public string VideoName { get; set; } = string.Empty;
    }
}
