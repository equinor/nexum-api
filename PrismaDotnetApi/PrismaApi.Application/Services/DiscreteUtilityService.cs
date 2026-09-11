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

public class DiscreteUtilityService : IDiscreteUtilityService
{
    private readonly IDiscreteUtilityRepository _discreteUtilityRepository;
    private readonly IMemoryCache _cache;

    public DiscreteUtilityService(IDiscreteUtilityRepository discreteUtilityRepository, IMemoryCache cache)
    {
        _discreteUtilityRepository = discreteUtilityRepository;
        _cache = cache;
    }

    public async Task<List<DiscreteUtilityDto>> CreateAsync(List<DiscreteUtilityDto> dtos, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities();
        await _discreteUtilityRepository.AddRangeAsync(entities, ct);
        return entities.ToDtos();
    }

    public async Task<List<DiscreteUtilityDto>> UpdateAsync(List<DiscreteUtilityDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntitiesWithoutParents();
        await _discreteUtilityRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _discreteUtilityRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _discreteUtilityRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<DiscreteUtilityDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _discreteUtilityRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToDtos();
    }

    public async Task<List<DiscreteUtilityDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _discreteUtilityRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetDiscreteUtilitiesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }

    private static Expression<Func<DiscreteUtility, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Utility!.Issue!.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<DiscreteUtility, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
