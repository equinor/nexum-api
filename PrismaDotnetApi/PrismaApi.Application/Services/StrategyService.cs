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
        var strategies = new List<StrategyOutgoingDto>();
        var projectIdsToGetFromDb = new HashSet<Guid>();

        var projectIds = _cache.GetAccessibleProjectIds(user);

        foreach (var projectId in projectIds)
        {
            var cachedStrategies = _cache.GetCacheItemAsStrategies(projectId, user);
            if (cachedStrategies != null)
            {
                strategies.AddRange(cachedStrategies);
            }
            else
            {
                projectIdsToGetFromDb.Add(projectId);
            }
        }
        if (projectIdsToGetFromDb.Count > 0)
        {
            var entities = await _strategyRepository.GetAllAsync(filterPredicate: ProjectFilter(projectIdsToGetFromDb), ct: ct);
            var dbStrategies = entities.ToOutgoingDtos();
            strategies.AddRange(dbStrategies);
            foreach (var projectId in projectIdsToGetFromDb)
            {
                var cacheKey = CacheKeys.GetStrategyInProjectKey(projectId);
                var projectStrategyDtos = strategies.Where(x => x.ProjectId == projectId).ToList();
                _cache.AddCacheItem(new CacheItem { CacheKey = cacheKey }, CacheConstants.DefaultQueryCacheInTimeSpan, projectStrategyDtos);
            }
        }

        return strategies;
    }

    private static Expression<Func<Strategy, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<Strategy, bool>> ProjectAndUserFilter(Guid projectId, UserOutgoingDto user)
        => e => e.ProjectId == projectId && e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
    private static Expression<Func<Strategy, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
