using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using System.Linq.Expressions;

namespace PrismaApi.Application.Services;

public class NodeService : INodeService
{
    private readonly INodeRepository _nodeRepository;
    private readonly IMemoryCache _cache;

    public NodeService(INodeRepository nodeRepository, IMemoryCache cache)
    {
        _nodeRepository = nodeRepository;
        _cache = cache;
    }

    public async Task<List<NodeOutgoingDto>> UpdateAsync(List<NodeIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities();
        await _nodeRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _nodeRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _nodeRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<NodeOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _nodeRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<NodeOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _nodeRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetNodesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }

    private static Expression<Func<Node, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Issue!.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<Node, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.Issue!.ProjectId);
}
