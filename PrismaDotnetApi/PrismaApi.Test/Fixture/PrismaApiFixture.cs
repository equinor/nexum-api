using Microsoft.Extensions.Caching.Memory;
using Microsoft.Extensions.DependencyInjection;
using PrismaApi.Domain.Constants;
using PrismaApi.Infrastructure.Context;
using PrismaApi.Test.Configuration;
using PrismaApi.Test.Configuration.User;
using PrismaApi.Test.Data;

namespace PrismaApi.Test.Fixture;

public class PrismaApiFixture : IAsyncLifetime
{
    public readonly PrismaWebAppFactory ApiFactory;

    public PrismaApiFixture()
    {
        ApiFactory = new PrismaWebAppFactory();

        PrismaUser = new TestPersonProfile
        {
            Id = Guid.NewGuid().ToString(),
            Name = "Test User A",
            Mail = "noreplyTestA@mail.com",
            Scopes = new[] { "Read" },
            Roles = new[] { AppRoles.PrismaDecisionUser }
        };

        SecondaryUser = new TestPersonProfile
        {
            Id = Guid.NewGuid().ToString(),
            Name = "Test User B",
            Mail = "noreplyTestB@mail.com",
            Scopes = new[] { "Read" },
            Roles = new[] { AppRoles.PrismaDecisionUser }
        };
    }

    public TestArguments TestArgs { get; set; } = new();

    public TestPersonProfile PrismaUser { get; }
    public TestPersonProfile SecondaryUser { get; }

    public Task InitializeAsync() => Task.CompletedTask;

    public async Task ResetDatabaseAsync()
    {
        using var scope = ApiFactory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var cache = scope.ServiceProvider.GetRequiredService<IMemoryCache>();

        if (cache is MemoryCache memoryCache)
        {
            memoryCache.Compact(1.0);
        }

        await db.Database.EnsureDeletedAsync();
        await db.Database.EnsureCreatedAsync();
        TestArgs = await TestModelBuilder.BuildFreshTestDataAsync(this);
    }

    public async Task DisposeAsync()
    {
        using var scope = ApiFactory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        await db.Database.EnsureDeletedAsync();
        GC.SuppressFinalize(db);
    }

    public TestClientScope UserScope() => new(PrismaUser);
    public TestClientScope SecondaryUserScope() => new(SecondaryUser);
}
