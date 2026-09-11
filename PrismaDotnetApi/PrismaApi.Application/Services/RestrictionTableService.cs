using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using PrismaApi.Infrastructure.Interfaces;
using System.Linq.Expressions;

namespace PrismaApi.Application.Services;

public class RestrictionTableService : IRestrictionTableService
{
    private readonly IRestrictionTableRepository _restrictionTableRepository;
    private readonly IDiscreteTableRuleEventHandler _discreteTableRuleEventHandler;
    private readonly IMemoryCache _cache;

    public RestrictionTableService(IRestrictionTableRepository restrictionTableRepository, IDiscreteTableRuleEventHandler discreteTableRuleEventHandler, IMemoryCache cache)
    {
        _restrictionTableRepository = restrictionTableRepository;
        _discreteTableRuleEventHandler = discreteTableRuleEventHandler;
        _cache = cache;
    }

    public async Task<List<RestrictionTableOutgoingDto>> CreateAsync(List<RestrictionTableIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _restrictionTableRepository.AddRangeAsync(entities, ct);
        var ids = dtos.Select(d => d.Id).ToList();
        _discreteTableRuleEventHandler.EnqueueRestrictionTablesForRebuild(ids);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<RestrictionTableOutgoingDto>> UpdateAsync(List<RestrictionTableIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _restrictionTableRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        _discreteTableRuleEventHandler.EnqueueRestrictionTablesForRebuild(ids);
        var updated = await _restrictionTableRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _restrictionTableRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<RestrictionTableOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _restrictionTableRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<RestrictionTableOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _restrictionTableRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetRestrictionTablesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }

    private static Expression<Func<RestrictionTable, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<RestrictionTable, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
