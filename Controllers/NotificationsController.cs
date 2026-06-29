using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Data;
using System.Security.Claims;
using System.Threading.Tasks;
using System.Linq;

namespace StudentEngagementSystem.Controllers
{
    [Authorize]
    public class NotificationsController : Controller
    {
        private readonly ApplicationDbContext _context;

        public NotificationsController(ApplicationDbContext context)
        {
            _context = context;
        }

        [HttpPost]
        public async Task<IActionResult> MarkAsRead(int id)
        {
            var teacherId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var notification = await _context.Notifications
                .FirstOrDefaultAsync(n => n.Id == id && n.TeacherId == teacherId);

            if (notification != null)
            {
                notification.IsRead = true;
                await _context.SaveChangesAsync();
                
                if (!string.IsNullOrEmpty(notification.LinkUrl))
                {
                    return Redirect(notification.LinkUrl);
                }
            }

            // Fallback redirect if no link is provided
            return RedirectToAction("Index", "Dashboard");
        }

        [HttpPost]
        public async Task<IActionResult> MarkAllAsRead()
        {
            var teacherId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var unreadNotifications = await _context.Notifications
                .Where(n => n.TeacherId == teacherId && !n.IsRead)
                .ToListAsync();

            if (unreadNotifications.Any())
            {
                foreach (var notification in unreadNotifications)
                {
                    notification.IsRead = true;
                }
                await _context.SaveChangesAsync();
            }

            return RedirectToAction("Index", "Dashboard");
        }
    }
}
