using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace StudentEngagementSystem.Models
{
    public class Video
    {
        [Key]
        public int VideoId { get; set; }

        [Required]
        public int StudentId { get; set; }

        [Required]
        [StringLength(255)]
        public string VideoName { get; set; } = string.Empty;

        [Required]
        [StringLength(500)]
        public string VideoPath { get; set; } = string.Empty;

        public DateTime UploadDate { get; set; } = DateTime.UtcNow;

        [StringLength(50)]
        public string? Duration { get; set; }

        // Navigation properties
        [ForeignKey("StudentId")]
        public virtual Student? Student { get; set; }

        public virtual AnalysisResult? AnalysisResult { get; set; }
    }
}
