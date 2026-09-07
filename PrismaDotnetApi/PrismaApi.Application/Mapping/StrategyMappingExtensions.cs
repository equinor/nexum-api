using System.Collections.Generic;
using System.Linq;
using PrismaApi.Domain.Dtos;
using PrismaApi.Domain.Entities;

namespace PrismaApi.Application.Mapping;

public static class StrategyMappingExtensions
{
    public static StrategyOutgoingDto ToOutgoingDto(this Strategy entity)
    {
        return new StrategyOutgoingDto
        {
            Id = entity.Id,
            ProjectId = entity.ProjectId,
            Name = entity.Name,
            Description = entity.Description,
            Rationale = entity.Rationale,
            Icon = entity.Icon,
            IconColor = entity.IconColor,
            Options = entity.StrategyOptions
                .Select(so => so.Option)
                .Where(option => option != null)
                .Select(option => option!.ToOutgoingDto())
                .ToList()
        };
    }

    public static List<StrategyOutgoingDto> ToOutgoingDtos(this IEnumerable<Strategy> entities)
    {
        return entities.Select(ToOutgoingDto).ToList();
    }

    public static Strategy ToEntity(this StrategyIncomingDto dto, UserOutgoingDto userDto)
    {
        return new Strategy
        {
            Id = dto.Id,
            ProjectId = dto.ProjectId,
            Name = dto.Name,
            Description = dto.Description,
            Rationale = dto.Rationale,
            CreatedById = userDto.Id,
            UpdatedById = userDto.Id,
            Icon = dto.Icon,
            IconColor = dto.IconColor,
            StrategyOptions = dto.Options.Select(option => new StrategyOption
            {
                ProjectId = dto.ProjectId,
                OptionId = option.Id,
                StrategyId = dto.Id
            }).ToList()
        };
    }

    public static List<Strategy> ToEntities(this IEnumerable<StrategyIncomingDto> dtos, UserOutgoingDto userDto)
    {
        return dtos.Select(dto => dto.ToEntity(userDto)).ToList();
    }
}
