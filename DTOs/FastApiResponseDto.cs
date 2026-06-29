using System.Text.Json.Serialization;

namespace StudentEngagementSystem.DTOs
{
    public class DisengagementIntervalDto
    {
        [JsonPropertyName("start")]
        public string Start { get; set; } = string.Empty;

        [JsonPropertyName("end")]
        public string End { get; set; } = string.Empty;
    }

    public class EmotionDistributionDto
    {
        [JsonPropertyName("neutral")]
        public double Neutral { get; set; }

        [JsonPropertyName("happy")]
        public double Happy { get; set; }

        [JsonPropertyName("sad")]
        public double Sad { get; set; }

        [JsonPropertyName("angry")]
        public double Angry { get; set; }

        [JsonPropertyName("fearful")]
        public double Fearful { get; set; }

        [JsonPropertyName("disgusted")]
        public double Disgusted { get; set; }

        [JsonPropertyName("surprised")]
        public double Surprised { get; set; }
    }

    public class TimelinePointDto
    {
        [JsonPropertyName("timestamp")]
        public double Timestamp { get; set; }

        [JsonPropertyName("isEngaged")]
        public bool IsEngaged { get; set; }

        [JsonPropertyName("engagement_score")]
        public double EngagementScore { get; set; }

        [JsonPropertyName("time")]
        public string Time { get; set; } = string.Empty;

        [JsonPropertyName("level")]
        public double Level { get; set; }
    }
    
    public class EmotionTimelinePointDto
    {
        [JsonPropertyName("time")]
        public string Time { get; set; } = string.Empty;
        
        [JsonPropertyName("emotion")]
        public string Emotion { get; set; } = string.Empty;
    }

    public class FastApiResponseDto
    {
        [JsonPropertyName("engagementPercentage")]
        public double EngagementPercentage { get; set; }

        [JsonPropertyName("focusedPercentage")]
        public double FocusedPercentage { get; set; }

        [JsonPropertyName("distractedPercentage")]
        public double DistractedPercentage { get; set; }

        [JsonPropertyName("dominantEmotion")]
        public string DominantEmotion { get; set; } = string.Empty;

        [JsonPropertyName("emotionDistribution")]
        public EmotionDistributionDto EmotionDistribution { get; set; } = new();

        [JsonPropertyName("engagementTimeline")]
        public List<TimelinePointDto> EngagementTimeline { get; set; } = new();

        [JsonPropertyName("emotionTimeline")]
        public List<EmotionTimelinePointDto> EmotionTimeline { get; set; } = new();

        [JsonPropertyName("disengagementIntervals")]
        public List<DisengagementIntervalDto> DisengagementIntervals { get; set; } = new();
    }
}
