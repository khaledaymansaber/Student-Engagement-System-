using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace StudentEngagementSystem.Models
{
    public class AnalysisResult
    {
        [Key]
        public int AnalysisId { get; set; }

        [Required]
        public int VideoId { get; set; }

        // Engagement Metrics (from blended prediction pipeline)
        public double EngagementPercentage { get; set; }
        public double FocusedPercentage { get; set; }
        public double DistractedPercentage { get; set; }

        // Raw Emotion Values (from HSE Emotion Model)
        public double EmotionNeutral { get; set; }
        public double EmotionHappy { get; set; }
        public double EmotionSad { get; set; }
        public double EmotionAngry { get; set; }
        public double EmotionFear { get; set; }
        public double EmotionDisgust { get; set; }
        public double EmotionSurprised { get; set; }

        // Mapped/Dominant Emotion
        [StringLength(50)]
        public string DominantEmotion { get; set; } = string.Empty;

        // JSON Serialized Timelines & Intervals
        public string DisengagementIntervals { get; set; } = "[]"; // List of intervals
        public string EngagementTimeline { get; set; } = "[]"; // Time vs Engagement Level
        public string EmotionTimeline { get; set; } = "[]"; // Time vs Emotion distribution

        [StringLength(500)]
        public string? JsonFilePath { get; set; }

        public DateTime CreatedDate { get; set; } = DateTime.UtcNow;

        // Navigation property
        [ForeignKey("VideoId")]
        public virtual Video? Video { get; set; }
    }
}
