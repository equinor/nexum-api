using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using System.Linq.Expressions;

namespace PrismaApi.Application.Services;

public class ObjectiveService : IObjectiveService
{
    private readonly IObjectiveRepository _objectiveRepository;
    private readonly IMemoryCache _cache;

    public ObjectiveService(IObjectiveRepository objectiveRepository, IMemoryCache cache)
    {
        _objectiveRepository = objectiveRepository;
        _cache = cache;
    }

    public async Task<List<ObjectiveOutgoingDto>> CreateAsync(List<ObjectiveIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _objectiveRepository.AddRangeAsync(entities, ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<ObjectiveOutgoingDto>> UpdateAsync(List<ObjectiveIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var entities = dtos.ToEntities(userDto);
        await _objectiveRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _objectiveRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _objectiveRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<ObjectiveOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var entities = await _objectiveRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return entities.ToOutgoingDtos();
    }

    public async Task<List<ObjectiveOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {

        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _objectiveRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetObjectivesInProjectKey,
            cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
            ct: ct);
    }
    public async Task<List<ObjectiveOutgoingDto>> GetByProjectAsync(Guid projectId, UserOutgoingDto user, CancellationToken ct = default)
    {
        var objectives = await _objectiveRepository.GetAllAsync(filterPredicate: ProjectAndUserFilter(projectId, user), ct: ct);
        return objectives.ToOutgoingDtos();
    }

    private static Expression<Func<Objective, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
    private static Expression<Func<Objective, bool>> ProjectAndUserFilter(Guid projectId, UserOutgoingDto user)
        => e => e.ProjectId == projectId && e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
    private static Expression<Func<Objective, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);

}
