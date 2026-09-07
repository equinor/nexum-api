using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;

namespace PrismaApi.Application.Services;

public class StrategyService : IStrategyService
{
    private readonly IStrategyRepository _strategyRepository;
    private readonly IMemoryCache _cache;

    public StrategyService(IStrategyRepository strategyRepository, IMemoryCache cache)
    {
        _strategyRepository = strategyRepository;
        _cache = cache;
    }

    public async Task<List<StrategyOutgoingDto>> CreateAsync(List<StrategyIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _strategyRepository.AddRangeAsync(entities, ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var created = await _strategyRepository.GetByIdsAsync(ids, ct: ct);
        return created.ToOutgoingDtos();
    }

    public async Task<List<StrategyOutgoingDto>> UpdateAsync(List<StrategyIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _strategyRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _strategyRepository.GetByIdsAsync(ids, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _strategyRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<StrategyOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var strategies = await _strategyRepository.GetByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
        return strategies.ToOutgoingDtos();
    }
    public async Task<List<StrategyOutgoingDto>> GetByProjectAsync(Guid projectId, UserOutgoingDto user, CancellationToken ct = default)
    {        
        var strategies = await _strategyRepository.GetAllAsync(filterPredicate: ProjectAndUserFilter(projectId, user), ct: ct);
        return strategies.ToOutgoingDtos();
    }

    public async Task<List<StrategyOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _strategyRepository.GetAllAsync(
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetStrategyInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }

    private static Expression<Func<Strategy, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<Strategy, bool>> ProjectAndUserFilter(Guid projectId, UserOutgoingDto user)
        => e => e.ProjectId == projectId && e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
    private static Expression<Func<Strategy, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
