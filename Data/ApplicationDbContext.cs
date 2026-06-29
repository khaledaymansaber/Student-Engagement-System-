using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Models;

namespace StudentEngagementSystem.Data
{
    public class ApplicationDbContext : IdentityDbContext<Teacher>
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<Student> Students { get; set; }
        public DbSet<Video> Videos { get; set; }
        public DbSet<AnalysisResult> AnalysisResults { get; set; }
        public DbSet<Notification> Notifications { get; set; }

        protected override void OnModelCreating(ModelBuilder builder)
        {
            base.OnModelCreating(builder);

            // Configure Teacher -> Student relationship
            builder.Entity<Student>()
                .HasOne(s => s.Teacher)
                .WithMany(t => t.Students)
                .HasForeignKey(s => s.TeacherId)
                .OnDelete(DeleteBehavior.Cascade);

            // Configure Student -> Video relationship
            builder.Entity<Video>()
                .HasOne(v => v.Student)
                .WithMany(s => s.Videos)
                .HasForeignKey(v => v.StudentId)
                .OnDelete(DeleteBehavior.Cascade);

            // Configure Video -> AnalysisResult one-to-one relationship
            builder.Entity<Video>()
                .HasOne(v => v.AnalysisResult)
                .WithOne(a => a.Video)
                .HasForeignKey<AnalysisResult>(a => a.VideoId)
                .OnDelete(DeleteBehavior.Cascade);

            // Configure Teacher -> Notification relationship
            builder.Entity<Notification>()
                .HasOne(n => n.Teacher)
                .WithMany() // Assuming Teacher doesn't have a Notifications collection explicitly, or you can map it later
                .HasForeignKey(n => n.TeacherId)
                .OnDelete(DeleteBehavior.Cascade);
        }
    }
}
