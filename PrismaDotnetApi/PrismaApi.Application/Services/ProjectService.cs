using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Constants;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;
using System.Linq.Expressions;

namespace PrismaApi.Application.Services;

public class ProjectService : IProjectService
{
    private readonly IProjectRepository _projectRepository;
    private readonly IProjectRoleRepository _projectRoleRepository;
    private readonly IUserRepository _userRepository;
    private readonly IBoardSheetRepository _boardSheetRepository;
    private readonly IMemoryCache _cache;

    public ProjectService(
        IProjectRepository projectRepository,
        IProjectRoleRepository projectRoleRepository,
        IUserRepository userRepository,
        IBoardSheetRepository boardSheetRepository,
        IMemoryCache cache)
    {
        _projectRepository = projectRepository;
        _projectRoleRepository = projectRoleRepository;
        _userRepository = userRepository;
        _cache = cache;
        _boardSheetRepository = boardSheetRepository;
    }

    public async Task<List<ProjectOutgoingDto>> CreateAsync(List<ProjectCreateDto> dtos, bool createDefaultRole, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var projectEntities = dtos.ToEntities(userDto);

        await _projectRepository.AddRangeAsync(projectEntities, ct);

        if (createDefaultRole)
        {

            var facilitatorRole = dtos.Select(x =>
            {
                return new ProjectRoleCreateDto
                {
                    Id = Guid.NewGuid(),
                    ProjectId = x.Id,
                    UserId = userDto.Id,
                    Role = ProjectRoleType.Facilitator.ToString()
                };
            }).Distinct();

            await _projectRoleRepository.AddRangeAsync(facilitatorRole.ToEntities(userDto), ct);
            await EnsureDefaultSheetsExists([.. projectEntities.Select(p => p.Id)], userDto, ct);
        }

        var ids = projectEntities.Select(p => p.Id).ToList();
        var projects = await _projectRepository.GetByIdsAsync(ids, withTracking: false, ct: ct);
        return projects.ToOutgoingDtos(userDto.Id);
    }

    public async Task<List<ProjectOutgoingDto>> UpdateAsync(List<ProjectIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
    {
        var userIds = dtos.SelectMany(d => d.Users).Select(u => new { u.UserId, u.Name }).Distinct();
        foreach (var u in userIds)
        {
            await _userRepository.GetOrAddByIdAsync(new UserIncomingDto { Id = u.UserId, Name = u.Name }, ct);
        }

        var projectEntities = dtos.ToEntities(userDto);
        var projects = await _projectRepository.UpdateRangeAsync(projectEntities, userDto, filterPredicate: UserFilter(userDto), ct);
        await EnsureDefaultSheetsExists([.. projectEntities.Select(p => p.Id)], userDto, ct);
        return projects.ToOutgoingDtos(userDto.Id);
    }

    public async Task<ProjectOutgoingDto?> UpdateFavoriteAsync(Guid id, bool favorite, UserOutgoingDto user, CancellationToken ct = default)
    {
        var updated = await _projectRoleRepository.UpdateFavoriteAsync(id, user.Id, favorite, ct);
        if (!updated)
            return null;

        var projects = await _projectRepository.GetByIdsAsync([id], withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return projects.FirstOrDefault()?.ToOutgoingDto(user.Id);
    }

    public async Task DeleteAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        await _projectRepository.DeleteByIdsAsync(ids, filterPredicate: UserFacilitatorFilter(user), ct: ct);
    }

    public async Task<List<ProjectOutgoingDto>> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var projects = await _projectRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        var dtos = projects.ToOutgoingDtos(user.Id);
        RegisterPublicProjectsInCache(dtos);
        return dtos;
    }

    public async Task<List<ProjectOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        var projects = await _cache.GetProjectScopedAsync(
            user,
            loadMissingAsync: async (projectIds, ct) => (
                await _projectRepository.GetAllAsync(
                    withTracking: false,
                    filterPredicate: project => projectIds.Contains(project.Id),
                    ct: ct
                )
            ).ToOutgoingDtos(user.Id),
            getProjectId: dto => dto.Id,
            getCacheKey: CacheKeys.GetProjectKey,
            cacheDuration: CacheConstants.DefaultLongQueryCacheInTimeSpan,
            ct: ct);

        RegisterPublicProjectsInCache(projects);
        return projects;
    }

    public async Task<List<PopulatedProjectDto>> GetPopulatedAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
    {
        var projects = await _projectRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);

        return projects.ToPopulatedDtos(user.Id);
    }

    public async Task<List<PopulatedProjectDto>> GetAllPopulatedAsync(UserOutgoingDto user, CancellationToken ct = default)
    {
        var projects = await _projectRepository.GetAllAsync(withTracking: false, filterPredicate: UserFilter(user), ct: ct);
        return projects.ToPopulatedDtos(user.Id);
    }

    private async Task EnsureDefaultSheetsExists(List<Guid> projectIds, UserOutgoingDto user, CancellationToken ct = default)
    {
        var existingSheets = await _boardSheetRepository.GetAllAsync(withTracking: false, filterPredicate: e => projectIds.Contains(e.ProjectId), ct: ct);
        var projectIdsWithSheets = existingSheets.Select(e => e.ProjectId).ToHashSet();
        var projectIdsWithoutSheets = projectIds.Except(projectIdsWithSheets).ToList();

        if (projectIdsWithoutSheets.Count > 0)
        {
            var defaultSheets = projectIdsWithoutSheets.Select(projectId => new BoardSheetIncomingDto
            {
                Id = Guid.NewGuid(),
                Name = DomainConstants.DefaultBoardSheetName,
                ProjectId = projectId
            }).ToList();
            await _boardSheetRepository.AddRangeAsync(defaultSheets.ToEntities(user), ct);
        }
    }

    private static Expression<Func<Project, bool>> UserFilter(UserOutgoingDto user)
        => e => e.Public || e.ProjectRoles.Any(p => p.UserId == user.Id);

    private static Expression<Func<Project, bool>> UserFacilitatorFilter(UserOutgoingDto user)
        => e => e.Public || e.ProjectRoles.Any(p => p.UserId == user.Id && p.Role == ProjectRoleType.Facilitator.ToString());

    private void RegisterPublicProjectsInCache(List<ProjectOutgoingDto> projects)
    {
        var publicProjectIds = projects.Where(p => p.Public).Select(p => p.Id).ToList();
        if (publicProjectIds.Count == 0) return;

        var existing = new HashSet<Guid>(_cache.GetPublicProjectIds());
        var previousCount = existing.Count;
        existing.UnionWith(publicProjectIds);

        if (existing.Count > previousCount)
        {
            _cache.AddCacheItem(new CacheItem { CacheKey = CacheKeys.PublicProjectIdsKey }, null, existing);
        }
    }
}
