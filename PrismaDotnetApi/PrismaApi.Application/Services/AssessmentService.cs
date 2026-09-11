using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Threading.Tasks;
using Microsoft.Extensions.Caching.Memory;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Application.Interfaces.Services;
using PrismaApi.Application.Mapping;
using PrismaApi.Domain.Constants;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Caching;

namespace PrismaApi.Application.Services
{
    public class AssessmentService : IAssessmentService
    {
        private readonly IAssessmentRepository _assessmentRepository;
        private readonly IProjectRoleRepository _projectRoleRepository;
        private readonly IMemoryCache _cache;
        public AssessmentService(IAssessmentRepository assessmentRepository, IProjectRoleRepository projectRoleRepository, IMemoryCache cache)
        {
            _assessmentRepository = assessmentRepository;
            _projectRoleRepository = projectRoleRepository;
            _cache = cache;
        }
        public async Task<List<AssessmentOutgoingDto>?> GetAsync(List<Guid> ids, UserOutgoingDto user, CancellationToken ct = default)
        {
            var entities = await _assessmentRepository.GetByIdsAsync(ids, withTracking: false, filterPredicate: UserFilter(user), ct: ct);
            if (entities == null || !entities.Any())
            {
                return null;
            }

            return entities.ToOutgoingDtos();
        }
        public async Task<List<AssessmentOutgoingDto>?> CreateAsync(List<AssessmentIncomingDto> dtos, UserOutgoingDto user, CancellationToken ct = default)
        {
            var projectIds = dtos.Select(d => d.ProjectId).Distinct().ToList();
            var roles = await _projectRoleRepository.GetAllAsync(
                withTracking: false,
                filterPredicate: r => projectIds.Contains(r.ProjectId) && r.UserId == user.Id.ToString() && r.Role == ProjectRoleType.Facilitator.ToString(),
                ct: ct);

            var accessibleProjectIds = roles.Select(r => r.ProjectId).Distinct().ToHashSet();
            if (!projectIds.All(id => accessibleProjectIds.Contains(id)))
            {
                throw new UnauthorizedAccessException("User is not a facilitator for the specified project(s).");
            }

            var assessment = dtos.ToEntities(user);
            var entities = await _assessmentRepository.AddRangeAsync(assessment, ct: ct);
            if (entities == null)
            {
                return null;
            }
            return entities.ToOutgoingDtos();
        }
        public async Task DeleteAsync(Guid id, UserOutgoingDto user, CancellationToken ct = default)
        {
            await _assessmentRepository.DeleteByIdsAsync(new List<Guid> { id }, filterPredicate: FacillitatorFilter(user), ct: ct);
        }

        public async Task<List<AssessmentOutgoingDto>> GetAllAsync(UserOutgoingDto user, CancellationToken ct = default)
        {
            return await _cache.GetProjectScopedAsync(
                user,
                loadMissingAsync: async (projectIds, ct) => (
                    await _assessmentRepository.GetAllAsync(
                        withTracking: false,
                        filterPredicate: ProjectFilter(projectIds),
                        ct: ct
                    )
                ).ToOutgoingDtos(),
                getProjectId: dto => dto.ProjectId,
                getCacheKey: CacheKeys.GetAssessmentKey,
                cacheDuration: CacheConstants.DefaultMediumQueryCacheInTimeSpan,
                ct: ct);
        }

        public async Task UpdateRangeAsync(List<AssessmentIncomingDto> dtos, UserOutgoingDto userDto, CancellationToken ct = default)
        {

            var entities = dtos.ToEntities(userDto);
            await _assessmentRepository.UpdateAsync(entities, filterPredicate: FacillitatorFilter(userDto), ct: ct);
        }
        private static Expression<Func<Assessment, bool>> FacillitatorFilter(UserOutgoingDto user)
            => e => e!.Project!.ProjectRoles.Any(p => p.UserId == user.Id.ToString() && p.Role == ProjectRoleType.Facilitator.ToString());
        private static Expression<Func<Assessment, bool>> UserFilter(UserOutgoingDto user)
            => e => e!.Project!.ProjectRoles.Any(p => p.UserId == user.Id);
        private static Expression<Func<Assessment, bool>> ProjectFilter(HashSet<Guid> projectIds)
            => e => projectIds.Contains(e.ProjectId);
    }
}
