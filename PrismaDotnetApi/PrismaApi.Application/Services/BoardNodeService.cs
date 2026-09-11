using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using System.Linq.Expressions;

namespace PrismaApi.Application.Services;

public class BoardNodeService : IBoardNodeService
{
    private readonly IBoardNodeRepository _boardNodeRepository;
    private readonly IMemoryCache _cache;

    public BoardNodeService(IBoardNodeRepository boardNodeRepository, IMemoryCache cache)
    {
        _boardNodeRepository = boardNodeRepository;
        _cache = cache;
    }

    public async Task<List<BoardNodeOutgoingDto>> CreateAsync(List<BoardNodeIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _boardNodeRepository.AddRangeAsync(entities, ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<BoardNodeOutgoingDto>> UpdateAsync(List<BoardNodeIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _boardNodeRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _boardNodeRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _boardNodeRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<BoardNodeOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _boardNodeRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<BoardNodeOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _boardNodeRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetBoardNodesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }

    private static Expression<Func<BoardNode, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<BoardNode, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
