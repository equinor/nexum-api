using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Domain.Dtos;

namespace PrismaApi.Infrastructure.Caching;

public static class MemoryCacheExtensions
{
    private static readonly HashSet<CacheItem> cachedKeys = new();
    private static readonly SemaphoreSlim cacheLock = new(100, 100);

    private static readonly MemoryCacheEntryOptions CacheEntryOptions =
        new MemoryCacheEntryOptions().SetSlidingExpiration(
            TimeSpan.FromMinutes(CacheConstants.DefaultMemoryCacheSlidingDurationInMinutes));

    public static object? GetCacheItem(this IMemoryCache cache, string cacheKey)
    {
        if (cache.TryGetValue(cacheKey, out var value))
        {
            return value;
        }

        return null;
    }

    public static T? GetCacheItem<T>(this IMemoryCache cache, string cacheKey) where T : class
    {
        if (cache.TryGetValue(cacheKey, out var value) && value is T typedValue)
        {
            return typedValue;
        }

        return null;
    }

    public static InfluenceDiagramDto? GetCacheItemAsInfluenceDiagram(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached diagram

        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<InfluenceDiagramDto>(CacheKeys.GetInfluenceDiagramKey(projectId));
    }

    public static List<IssueOutgoingDto>? GetCacheItemAsIssues(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached issues

        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<IssueOutgoingDto>>(CacheKeys.GetIssuesInProjectKey(projectId));
    }

    public static List<EdgeOutgoingDto>? GetCacheItemAsEdges(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached edges

        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<EdgeOutgoingDto>>(CacheKeys.GetEdgesInProjectKey(projectId));
    }

    public static List<NodeOutgoingDto>? GetCacheItemAsNodes(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached nodes

        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<NodeOutgoingDto>>(CacheKeys.GetNodesInProjectKey(projectId));
    }

    public static List<BoardNodeOutgoingDto>? GetCacheItemAsBoardNodes(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached board nodes
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<BoardNodeOutgoingDto>>(CacheKeys.GetBoardNodesInProjectKey(projectId));
    }

    public static List<BoardSheetOutgoingDto>? GetCacheItemAsBoardSheets(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached board sheets
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<BoardSheetOutgoingDto>>(CacheKeys.GetBoardSheetsInProjectKey(projectId));
    }

    public static List<AssessmentOutgoingDto>? GetCacheItemAsAssessment(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached assessment
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<AssessmentOutgoingDto>>(CacheKeys.GetAssessmentKey(projectId));
    }

    public static List<DiscreteProbabilityDto>? GetCacheItemAsDiscreteProbabilities(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached discrete probabilities
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<DiscreteProbabilityDto>>(CacheKeys.GetDiscreteProbabilitiesInProjectKey(projectId));
    }

    public static List<DiscreteUtilityDto>? GetCacheItemAsDiscreteUtilities(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached discrete utilities
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<DiscreteUtilityDto>>(CacheKeys.GetDiscreteUtilitiesInProjectKey(projectId));
    }

    public static List<RestrictionTableOutgoingDto>? GetCacheItemAsRestrictionTables(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached restriction tables
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<RestrictionTableOutgoingDto>>(CacheKeys.GetRestrictionTablesInProjectKey(projectId));
    }

    public static List<ObjectiveOutgoingDto>? GetCacheItemAsObjectives(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached objectives
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<ObjectiveOutgoingDto>>(CacheKeys.GetObjectivesInProjectKey(projectId));
    }

    public static List<StrategyOutgoingDto>? GetCacheItemAsStrategies(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached strategies
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<StrategyOutgoingDto>>(CacheKeys.GetStrategyInProjectKey(projectId));
    }

    public static List<ProjectOutgoingDto>? GetCacheItemAsProjects(this IMemoryCache cache, Guid projectId, UserOutgoingDto user)
    {
        // check that the user has access to the project before returning cached projects
        if (!cache.HasAccessToProject(user, projectId))
        {
            return null;
        }
        return cache.GetCacheItem<List<ProjectOutgoingDto>>(CacheKeys.GetProjectKey(projectId));
    }

    public static HashSet<Guid> GetPublicProjectIds(this IMemoryCache cache)
    {
        // check that the user has access to the public projects before returning cached public project ids
        return cache.GetCacheItem<HashSet<Guid>>(CacheKeys.PublicProjectIdsKey) ?? new HashSet<Guid>();
    }

    public static HashSet<Guid> GetAccessibleProjectIds(this IMemoryCache cache, UserOutgoingDto user)
    {
        var projectIds = user.ProjectRoles.Select(r => r.ProjectId).ToHashSet();
        projectIds.UnionWith(cache.GetPublicProjectIds());
        return projectIds;
    }

    public static void UpdatePublicProjectIds(this IMemoryCache cache, HashSet<Guid> idsToRemove, HashSet<Guid> idsToAdd)
    {
        cacheLock.Wait();
        try
        {
            var publicProjectIds = new HashSet<Guid>(cache.GetPublicProjectIds());
            publicProjectIds.ExceptWith(idsToRemove);
            publicProjectIds.UnionWith(idsToAdd);
            cache.Set(CacheKeys.PublicProjectIdsKey, publicProjectIds, CacheEntryOptions);
        }
        finally
        {
            _ = cacheLock.Release();
        }
    }


    public static void AddCacheItem(this IMemoryCache cache, CacheItem key, TimeSpan? duration,
        object? value)
    {
        // We do not want to cache null values
        if (value is null)
        {
            return;
        }

        cacheLock.Wait();
        try
        {

            if (duration.HasValue)
            {
                _ = cache.Set(key.CacheKey, value, duration.Value);
            }
            else
            {
                // Create cache entry with sliding expiration for all entries not having a duration provided. This to prevent cache to always grow.
                _ = cache.Set(key.CacheKey, value, CacheEntryOptions);
            }

            _ = cachedKeys.Add(key);
        }
        finally
        {
            _ = cacheLock.Release();
        }
    }

    public static void InvalidateCacheEntry(this IMemoryCache cache, CacheItem cacheItem)
    {
        cacheLock.Wait();
        try
        {
            if (cacheItem.IsGlobal)
            {
                cache.InvalidateGloballyCachedQueries();
            }
            else
            {
                cache.InvalidateCachedQueriesByKey(cacheItem);
            }
        }
        finally
        {
            _ = cacheLock.Release();
        }
    }

    public static void InvalidateAllCachedQueries(this IMemoryCache cache)
    {
        var keysToInvalidate = cachedKeys.ToList();

        InvalidateCacheKeys(cache, keysToInvalidate);
    }

    private static void InvalidateGloballyCachedQueries(this IMemoryCache cache)
    {
        var keysToInvalidate = cachedKeys
            .Where(key => key.IsGlobal)
            .ToList();

        InvalidateCacheKeys(cache, keysToInvalidate);
    }

    private static void InvalidateCachedQueriesByKey(this IMemoryCache cache, CacheItem cacheKey)
    {
        var keysToInvalidate = cachedKeys
            .Where(key => key.IsGlobal == false && key.CacheKey == cacheKey.CacheKey);

        InvalidateCacheKeys(cache, keysToInvalidate);
    }

    private static void InvalidateCacheKeys(IMemoryCache cache,
        IEnumerable<CacheItem> keysToInvalidate)
    {
        foreach (var key in keysToInvalidate)
        {
            cache.Remove(key.CacheKey);
            _ = cachedKeys.Remove(key);
        }
    }

    public static double GetApproximateCacheSizeInMB(this IMemoryCache cache)
    {
        long totalBytes = 0;
        foreach (var key in cachedKeys)
        {
            var value = cache.GetCacheItem(key.CacheKey);
            if (value is not null)
            {
                var json = System.Text.Json.JsonSerializer.SerializeToUtf8Bytes(value);
                totalBytes += json.Length;
            }
        }
        return Math.Round(totalBytes / (1024.0 * 1024.0), 4);
    }

    private static bool HasAccessToProject(this IMemoryCache cache, UserOutgoingDto user, Guid projectId)
    {
        if (user.ProjectRoles.Any(pr => pr.ProjectId == projectId))
            return true;

        var publicIds = cache.GetCacheItem<HashSet<Guid>>(CacheKeys.PublicProjectIdsKey);
        return publicIds?.Contains(projectId) == true;
    }

    ///<summary>
    /// Retrieves project-scoped cached items, loading missing items as needed.
    /// <param name="user">The user for whom to retrieve cached items.</param>
    /// <param name="loadMissingAsync">Function to load missing items from the database.</param>
    /// <param name="getProjectId">Function to get the project ID from a DTO.</param>
    /// <param name="getCacheKey">Function to get the cache key for a project ID.</param>
    /// <param name="cacheDuration">Duration to cache the items.</param>
    /// <param name="ct">Cancellation token.</param>
    /// </summary>
    public static async Task<List<TDto>> GetProjectScopedAsync<TDto>(
    this IMemoryCache cache,
    UserOutgoingDto user,
    Func<HashSet<Guid>, CancellationToken, Task<List<TDto>>> loadMissingAsync,
    Func<TDto, Guid> getProjectId,
    Func<Guid, string> getCacheKey,
    TimeSpan cacheDuration,
    CancellationToken ct = default)
    where TDto : class
    {
        var results = new List<TDto>();
        var projectIdsToLoad = new HashSet<Guid>();

        foreach (var projectId in cache.GetAccessibleProjectIds(user))
        {
            var cachedDtos = cache.GetCacheItem<List<TDto>>(getCacheKey(projectId));
            if (cachedDtos is not null)
            {
                results.AddRange(cachedDtos);
            }
            else
            {
                projectIdsToLoad.Add(projectId);
            }
        }

        if (projectIdsToLoad.Count == 0)
        {
            return results;
        }

        var loadedDtos = await loadMissingAsync(projectIdsToLoad, ct);
        results.AddRange(loadedDtos);

        foreach (var projectId in projectIdsToLoad)
        {
            var projectDtos = loadedDtos.Where(dto => getProjectId(dto) == projectId).ToList();
            cache.AddCacheItem(
                new CacheItem { CacheKey = getCacheKey(projectId) },
                cacheDuration,
                projectDtos);
        }

        return results;
    }
}
