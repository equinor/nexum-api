using System.Collections.Generic;
using System.Linq.Expressions;
using System.Threading.Tasks;

namespace PrismaApi.Application.Interfaces.Repositories;

public interface ICrudRepository<TEntity, TId>
    where TEntity : class
    where TId : notnull
{
    Task<TEntity?> GetByIdAsync(TId id, bool withTracking = true, IQueryable<TEntity>? customQuery = null, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default);
    Task<List<TEntity>> GetByIdsAsync(IEnumerable<TId> ids, bool withTracking = true, IQueryable<TEntity>? customQuery = null, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default);
    Task<List<TEntity>> GetAllAsync(bool withTracking = true, IQueryable<TEntity>? customQuery = null, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default);
    Task<TEntity> AddAsync(TEntity entity, CancellationToken ct = default);
    Task<List<TEntity>> AddRangeAsync(IEnumerable<TEntity> entities, CancellationToken ct = default);
    Task UpdateRangeAsync(IEnumerable<TEntity> entities, CancellationToken ct = default);
    Task DeleteByIdsAsync(IEnumerable<TId> ids, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default);
    Task DeleteFromPredicateAsync(Expression<Func<TEntity, bool>> filterPredicate, CancellationToken ct = default);
}
