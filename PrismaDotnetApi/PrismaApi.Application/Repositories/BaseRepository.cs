using Microsoft.EntityFrameworkCore;
using PrismaApi.Application.Exceptions;
using PrismaApi.Application.Interfaces.Repositories;
using PrismaApi.Domain.Interfaces;
using PrismaApi.Infrastructure.Context;
using PrismaApi.Infrastructure.Extensions;
using System.Linq.Expressions;

namespace PrismaApi.Application.Repositories;

public class BaseRepository<TEntity, TId> : ICrudRepository<TEntity, TId>
    where TEntity : class, IBaseEntity<TId>
    where TId : notnull
{
    protected readonly AppDbContext DbContext;
    protected readonly DbSet<TEntity> Set;

    public BaseRepository(AppDbContext dbContext)
    {
        DbContext = dbContext;
        Set = dbContext.Set<TEntity>();
    }

    protected virtual IQueryable<TEntity> Query()
    {
        return Set.AsQueryable();
    }

    public virtual Task<TEntity?> GetByIdAsync(TId id, bool withTracking = true, IQueryable<TEntity>? customQuery = null, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default)
    {
        IQueryable<TEntity> query = customQuery ?? Query();
        query = query.OptionalWhere(filterPredicate);

        if (!withTracking)
        {
            query = query.AsNoTracking();
        }

        return query
            .FirstOrDefaultAsync(e => e.Id.Equals(id), ct);
    }

    public virtual Task<List<TEntity>> GetByIdsAsync(IEnumerable<TId> ids, bool withTracking = true, IQueryable<TEntity>? customQuery = null, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default)
    {
        var idList = ids.ToList();
        if (idList.Count == 0)
        {
            return Task.FromResult(new List<TEntity>());
        }

        IQueryable<TEntity> query = customQuery ?? Query();
        query = query.OptionalWhere(filterPredicate);

        if (!withTracking)
        {
            query = query.AsNoTracking();
        }

        return query
            .Where(e => idList.Contains(e.Id))
            .ToListAsync(ct);
    }

    public virtual async Task<List<TEntity>> GetAllAsync(bool withTracking = true, IQueryable<TEntity>? customQuery = null, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default)
    {
        IQueryable<TEntity> query = customQuery ?? Query();
        query = query.OptionalWhere(filterPredicate);

        if (!withTracking)
        {
            query = query.AsNoTracking();
        }
        return await query.ToListAsync(ct);
    }

    public virtual async Task<TEntity> AddAsync(TEntity entity, CancellationToken ct = default)
    {
        Set.Add(entity);
        DbContext.Entry(entity).State = EntityState.Added;
        await DbContext.SaveChangesAsync(ct);
        return entity;
    }

    public virtual async Task<List<TEntity>> AddRangeAsync(IEnumerable<TEntity> entities, CancellationToken ct = default)
    {
        var list = entities.ToList();
        Set.AddRange(list);
        foreach (var entity in list)
        {
            DbContext.Entry(entity).State = EntityState.Added;
        }
        await DbContext.SaveChangesAsync(ct);
        return list;
    }

    public virtual async Task UpdateRangeAsync(IEnumerable<TEntity> entities, CancellationToken ct = default)
    {
        Set.UpdateRange(entities);
        foreach (var entity in entities)
        {
            DbContext.Entry(entity).State = EntityState.Modified;
        }
        await DbContext.SaveChangesAsync(ct);
    }

    public virtual async Task DeleteByIdsAsync(IEnumerable<TId> ids, Expression<Func<TEntity, bool>>? filterPredicate = null, CancellationToken ct = default)
    {
        var entities = await Set
            .OptionalWhere(filterPredicate)
            .Where(e => ids.ToList().Contains(e.Id))
            .ToListAsync(ct);

        if (entities.Count == 0)
        {
            throw new NotFoundException($"No {typeof(TEntity).Name} entities found. Either the entities do not exist or the user does not have permission to delete them.");
        }

        Set.RemoveRange(entities);
        foreach (var entity in entities)
        {
            DbContext.Entry(entity).State = EntityState.Deleted;
        }
        await DbContext.SaveChangesAsync(ct);
    }

    public virtual async Task DeleteFromPredicateAsync(Expression<Func<TEntity, bool>> filterPredicate, CancellationToken ct = default)
    {
        var entities = await Set
            .OptionalWhere(filterPredicate)
            .ToListAsync(ct);

        if (entities.Count == 0)
        {
            throw new NotFoundException($"No {typeof(TEntity).Name} entities found. Either the entities do not exist or the user does not have permission to delete them.");
        }

        Set.RemoveRange(entities);
        foreach (var entity in entities)
        {
            DbContext.Entry(entity).State = EntityState.Deleted;
        }
        await DbContext.SaveChangesAsync(ct);
    }
}
