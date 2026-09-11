using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Constants;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Interfaces;
using PrismaApi.Infrastructure.Caching;
using System.Linq.Expressions;
using PrismaApi.Application.Exceptions;

namespace PrismaApi.Application.Services;

public class IssueService : IIssueService
{
    private readonly IIssueRepository _issueRepository;
    private readonly IProjectRepository _projectRepository;
    private readonly IEdgeRepository _edgeRepository;
    private readonly IDiscreteTableRuleEventHandler _discreteTableRuleEventHandler;
    private readonly IMemoryCache _cache;

    public IssueService(IIssueRepository issueRepository, IProjectRepository projectRepository, IEdgeRepository edgeRepository, IDiscreteTableRuleEventHandler discreteTableRuleEventHandler, IMemoryCache cache)
    {
        _issueRepository = issueRepository;
        _projectRepository = projectRepository;
        _edgeRepository = edgeRepository;
        _discreteTableRuleEventHandler = discreteTableRuleEventHandler;
        _cache = cache;
    }

    public async Task<List<IssueOutgoingDto>> CreateAsync(List<IssueIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var projectIds = dtos.Select(d => d.ProjectId).Distinct().ToList();
        if ((await _projectRepository.GetProjectsWhereUserHasAccess(projectIds, userDto.Id, ct)).Count == 0)
            throw new UnauthorizedAccessException("User does not have access to one or more projects.");

        EnsureNodeDefaults(dtos);
        var entities = dtos.ToEntities(userDto);
        await _issueRepository.AddRangeAsync(entities, ct);
        foreach (var entity in entities)
        {
            if (entity.Type == IssueType.Uncertainty.ToString() && entity.Uncertainty?.Outcomes.Count > 0)
            {
                _discreteTableRuleEventHandler.EnqueueIssuesForRebuild([entity.Id]);
            }
        }
        return entities.ToOutgoingDtos();
    }

    public async Task<List<IssueOutgoingDto>> UpdateAsync(List<IssueIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        EnsureNodeDefaults(dtos);
        var entities = dtos.ToEntities(userDto);
        await _issueRepository.UpdateRangeAsync(entities, UserFilter(userDto), ct);
        var ids = dtos.Select(d => d.Id).ToList();
        var updated = await _issueRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(userDto), ct: ct);
        return updated.ToOutgoingDtos();
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        // Remove edges connected to these issues before deleting them
        try
        {
            await _edgeRepository.DeleteFromPredicateAsync(e => ids.Contains(e.HeadNode!.IssueId), ct);
        }
        catch (NotFoundException)
        {
            // Ignore if no edges were found to delete
        }
        await _issueRepository.DeleteByIdsAsync(ids, filterPredicate: UserFilter(user), ct: ct);
    }

    public async Task<List<IssueOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var issues = await _issueRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return issues.ToOutgoingDtos();
    }

    public async Task<List<IssueOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        return await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _issueRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: ProjectFilter(projectIds),
                    ct: ct
                )
            ).ToOutgoingDtos(),
            getProjectId: dto => dto.ProjectId,
            getCacheKey: CacheKeys.GetIssuesInProjectKey,
            cacheDuration: CacheConstants.DefaultLongQueryCacheInTimeSpan,
            ct: ct);
    }

    private static void EnsureNodeDefaults(IEnumerable<IssueIncomingDto> dtos)
    {
        foreach (var dto in dtos)
        {
            if (dto.Node != null)
            {
                if (dto.Node.NodeStyle == null)
                {
                    dto.Node.NodeStyle = new NodeStyleIncomingDto
                    {
                        Id = Guid.NewGuid(),
                        NodeId = dto.Node.Id
                    };
                }

                continue;
            }

            var nodeId = Guid.NewGuid();
            dto.Node = new NodeIncomingDto
            {
                Id = nodeId,
                ProjectId = dto.ProjectId,
                IssueId = dto.Id,
                NodeStyle = new NodeStyleIncomingDto
                {
                    Id = Guid.NewGuid(),
                    NodeId = nodeId
                }
            };
        }
    }
    private static Expression<Func<Issue, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
    private static Expression<Func<Issue, bool>> ProjectFilter(HashSet<Guid> projectIds)
        => e => projectIds.Contains(e.ProjectId);
}
