using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using StudentEngagementSystem.Data;
using StudentEngagementSystem.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlServer(connectionString));

builder.Services.AddDatabaseDeveloperPageExceptionFilter();

builder.Services.AddDefaultIdentity<Teacher>(options => {
    options.SignIn.RequireConfirmedAccount = false;
    options.Password.RequireDigit = true;
    options.Password.RequiredLength = 6;
    options.Password.RequireNonAlphanumeric = false;
    options.Password.RequireUppercase = false;
    options.Password.RequireLowercase = false;
})
.AddEntityFrameworkStores<ApplicationDbContext>();

builder.Services.ConfigureApplicationCookie(options =>
{
    options.LoginPath = "/Account/Login";
    options.LogoutPath = "/Account/Logout";
    options.AccessDeniedPath = "/Account/AccessDenied";
});

builder.Services.AddControllersWithViews();

// Register Repositories
builder.Services.AddScoped<StudentEngagementSystem.Repositories.Interfaces.IStudentRepository, StudentEngagementSystem.Repositories.StudentRepository>();
builder.Services.AddScoped<StudentEngagementSystem.Repositories.Interfaces.IVideoRepository, StudentEngagementSystem.Repositories.VideoRepository>();
builder.Services.AddScoped<StudentEngagementSystem.Repositories.Interfaces.IAnalysisResultRepository, StudentEngagementSystem.Repositories.AnalysisResultRepository>();

// Register Services
builder.Services.AddHttpClient<StudentEngagementSystem.Services.Interfaces.IAIAnalysisService, StudentEngagementSystem.Services.AIAnalysisService>(client =>
{
    client.Timeout = TimeSpan.FromMinutes(10); // Video analysis can take several minutes
});

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseMigrationsEndPoint();
}
else
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    // app.UseHsts(); // Disabled since no-https
}

// app.UseHttpsRedirection(); // Disabled since no-https
app.UseStaticFiles();

app.UseRouting();

app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Dashboard}/{action=Index}/{id?}");
app.MapRazorPages(); // For Identity UI

app.Run();
