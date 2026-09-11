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

public class DiscreteProbabilityService: IDiscreteProbabilityService
{
    private readonly IDiscreteProbabilityRepository _discreteProbabilityRepository;
    private readonly IMemoryCache _cache;

    public DiscreteProbabilityService(IDiscreteProbabilityRepository discreteProbabilityRepository, IMemoryCache cache)
    {
        _discreteProbabilityRepository = discreteProbabilityRepository;
        _cache = cache;
    }

    public async Task<List<DiscreteProbabilityDto>> CreateAsync(List<DiscreteProbabilityDto> dtos, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities();
        await _discreteProbabilityRepository.AddRangeAsync(entities, ct);
        return entities.ToDtos();
    }

    public async Task<List<DiscreteProbabilityDto>> UpdateAsync(List<DiscreteProbabilityDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntitiesWithoutParents();
        await _discreteProbabilityRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _discreteProbabilityRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _discreteProbabilityRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<DiscreteProbabilityDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _discreteProbabilityRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToDtos();
    }

    public async Task<List<DiscreteProbabilityDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _discreteProbabilityRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetDiscreteProbabilitiesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }

    private static Expression<Func<DiscreteProbability, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Uncertainty!.Issue!.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<DiscreteProbability, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
