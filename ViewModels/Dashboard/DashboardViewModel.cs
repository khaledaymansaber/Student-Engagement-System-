using StudentEngagementSystem.Models;

namespace StudentEngagementSystem.ViewModels.Dashboard
{
    public class DashboardViewModel
    {
        public int TotalStudents { get; set; }
        public int TotalVideos { get; set; }
        public int AnalyzedVideos { get; set; }
        public IEnumerable<Student> RecentStudents { get; set; } = new List<Student>();
        public IEnumerable<Video> RecentVideos { get; set; } = new List<Video>();
    }
}
