using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Data;
using System.Linq;
using System.Security.Claims;
using System.Threading.Tasks;

namespace StudentEngagementSystem.ViewComponents
{
    public class NotificationsViewComponent : ViewComponent
    {
        private readonly ApplicationDbContext _context;

        public NotificationsViewComponent(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<IViewComponentResult> InvokeAsync()
        {
            var teacherId = HttpContext.User.FindFirstValue(ClaimTypes.NameIdentifier);
            
            if (string.IsNullOrEmpty(teacherId))
            {
                return View(Enumerable.Empty<StudentEngagementSystem.Models.Notification>());
            }

            var notifications = await _context.Notifications
                .Where(n => n.TeacherId == teacherId)
                .OrderByDescending(n => n.CreatedAt)
                .Take(5)
                .ToListAsync();

            return View(notifications);
        }
    }
}
