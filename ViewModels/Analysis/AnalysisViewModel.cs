using StudentEngagementSystem.Models;
using System.Collections.Generic;

namespace StudentEngagementSystem.ViewModels.Analysis
{
    public class AnalysisViewModel
    {
        public Video Video { get; set; } = default!;
        public AnalysisResult AnalysisResult { get; set; } = default!;
        public Student Student { get; set; } = default!;
        public List<Student> StudentsList { get; set; } = new List<Student>();
        
        // Formatted strings for Chart.js
        public string EngagementTimelineJson { get; set; } = "[]";
        public string EmotionTimelineJson { get; set; } = "[]";
        public string DisengagementIntervalsJson { get; set; } = "[]";
    }
}
