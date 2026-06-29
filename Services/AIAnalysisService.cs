using System.Text.Json;
using StudentEngagementSystem.DTOs;
using StudentEngagementSystem.Services.Interfaces;

namespace StudentEngagementSystem.Services
{
    public class AIAnalysisService : IAIAnalysisService
    {
        private readonly HttpClient _httpClient;
        private readonly IConfiguration _configuration;
        private readonly ILogger<AIAnalysisService> _logger;
        private readonly bool _useMockData;

        public AIAnalysisService(HttpClient httpClient, IConfiguration configuration, ILogger<AIAnalysisService> logger)
        {
            _httpClient = httpClient;
            _configuration = configuration;
            _logger = logger;
            
            var baseUrl = _configuration["AISettings:BaseUrl"] ?? "http://localhost:8000";
            _httpClient.BaseAddress = new Uri(baseUrl);
            
            _useMockData = _configuration.GetValue<bool>("AISettings:UseMockData");
        }

        public async Task<FastApiResponseDto?> AnalyzeVideoAsync(string videoPath)
        {
            if (_useMockData)
            {
                return await GenerateMockDataAsync(videoPath);
            }

            try
            {
                using var form = new MultipartFormDataContent();
                using var fileStream = new FileStream(videoPath, FileMode.Open, FileAccess.Read);
                var fileContent = new StreamContent(fileStream);
                
                // Content-Type might be inferred, but good to be explicit based on extension
                var mimeType = "video/mp4";
                if (videoPath.EndsWith(".avi", StringComparison.OrdinalIgnoreCase)) mimeType = "video/x-msvideo";
                if (videoPath.EndsWith(".mov", StringComparison.OrdinalIgnoreCase)) mimeType = "video/quicktime";
                
                fileContent.Headers.ContentType = new System.Net.Http.Headers.MediaTypeHeaderValue(mimeType);
                
                form.Add(fileContent, "file", Path.GetFileName(videoPath));

                var response = await _httpClient.PostAsync("/predict", form);

                if (response.IsSuccessStatusCode)
                {
                    var jsonResponse = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<FastApiResponseDto>(jsonResponse, new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    });
                    return result;
                }
                else
                {
                    _logger.LogWarning("FastAPI returned non-success status code: {StatusCode}", response.StatusCode);
                    return null;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error communicating with FastAPI server");
                return null;
            }
        }

        public async Task<bool> IsServiceAvailableAsync()
        {
            if (_useMockData) return true;

            try
            {
                var response = await _httpClient.GetAsync("/health"); // Assuming a health endpoint
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private async Task<FastApiResponseDto> GenerateMockDataAsync(string videoPath)
        {
            _logger.LogInformation("Using MOCK AI analysis for video: {VideoPath}", videoPath);
            
            // Simulate 2-3 seconds processing delay
            var rnd = new Random();
            await Task.Delay(rnd.Next(2000, 3000));

            var eng = rnd.NextDouble() * 40 + 50; // 50 to 90
            var foc = rnd.NextDouble() * (eng - 10) + 10;
            var dist = 100 - foc;

            var e1 = rnd.NextDouble() * 30 + 20;
            var e2 = rnd.NextDouble() * 30 + 10;
            var e3 = rnd.NextDouble() * 10;
            var e4 = rnd.NextDouble() * 5;
            var e5 = rnd.NextDouble() * 5;
            var e6 = rnd.NextDouble() * 5;
            var sum = e1 + e2 + e3 + e4 + e5 + e6;
            var e7 = 100 - sum;

            var emotions = new Dictionary<string, double>
            {
                { "Neutral", e1 },
                { "Happy", e2 },
                { "Sad", e3 },
                { "Angry", e4 },
                { "Fearful", e5 },
                { "Disgusted", e6 },
                { "Surprised", e7 }
            };

            var dominant = emotions.OrderByDescending(e => e.Value).First().Key;

            var engagementTimeline = new List<TimelinePointDto>();
            var emotionTimeline = new List<EmotionTimelinePointDto>();
            
            var emotionKeys = emotions.Keys.ToList();

            for (int i = 1; i <= 10; i++)
            {
                var timeStr = $"00:{i:D2}";
                
                // Random walk around overall engagement
                var pt = eng + (rnd.NextDouble() * 20 - 10);
                if (pt > 100) pt = 100;
                if (pt < 0) pt = 0;
                
                engagementTimeline.Add(new TimelinePointDto { Time = timeStr, Level = Math.Round(pt, 1) });
                
                // Mostly dominant emotion, occasionally random
                var em = rnd.NextDouble() > 0.3 ? dominant : emotionKeys[rnd.Next(emotionKeys.Count)];
                emotionTimeline.Add(new EmotionTimelinePointDto { Time = timeStr, Emotion = em });
            }

            var intervals = new List<DisengagementIntervalDto>();
            if (rnd.NextDouble() > 0.5)
            {
                intervals.Add(new DisengagementIntervalDto { Start = $"00:0{rnd.Next(1, 4)}", End = $"00:0{rnd.Next(5, 7)}" });
            }

            return new FastApiResponseDto
            {
                EngagementPercentage = Math.Round(eng, 1),
                FocusedPercentage = Math.Round(foc, 1),
                DistractedPercentage = Math.Round(dist, 1),
                DominantEmotion = dominant,
                EmotionDistribution = new EmotionDistributionDto
                {
                    Neutral = Math.Round(emotions["Neutral"], 1),
                    Happy = Math.Round(emotions["Happy"], 1),
                    Sad = Math.Round(emotions["Sad"], 1),
                    Angry = Math.Round(emotions["Angry"], 1),
                    Fearful = Math.Round(emotions["Fearful"], 1),
                    Disgusted = Math.Round(emotions["Disgusted"], 1),
                    Surprised = Math.Round(emotions["Surprised"], 1)
                },
                DisengagementIntervals = intervals,
                EngagementTimeline = engagementTimeline,
                EmotionTimeline = emotionTimeline
            };
        }
    }
}
