using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using System.Linq.Expressions;

namespace PrismaApi.Application.Services;

public class EdgeService : IEdgeService
{
    private readonly IEdgeRepository _edgeRepository;
    private readonly IMemoryCache _cache;

    public EdgeService(IEdgeRepository edgeRepository, IMemoryCache cache)
    {
        _edgeRepository = edgeRepository;
        _cache = cache;
    }

    public async Task<List<EdgeOutgoingDto>> CreateAsync(List<EdgeIncomingDto> dtos, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities();
        await _edgeRepository.AddRangeAsync(entities, ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var created = await _edgeRepository.GetByIdsAsync(ids, withTracking: false, ct: ct);
        return created.ToOutgoingDtos();
    }

    public async Task<List<EdgeOutgoingDto>> UpdateAsync(List<EdgeIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities();
        await _edgeRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _edgeRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _edgeRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<EdgeOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _edgeRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<EdgeOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _edgeRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetEdgesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }
    private static Expression<Func<Edge, bool>> UserFilter(UserOutgoingDto user)
        => e => e.HeadNode!.Issue!.Project!.ProjectRoles.Any(p => p.UserId == user.Id) && e.TailNode!.Issue!.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
    private static Expression<Func<Edge, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
