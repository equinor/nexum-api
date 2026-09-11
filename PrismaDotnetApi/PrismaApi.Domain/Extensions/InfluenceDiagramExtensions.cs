using System.Text.Json;
using PrismaApi.Domain.Constants;
using PrismaApi.Domain.Dtos;

namespace PrismaApi.Domain.Extensions;

public static class InfluenceDiagramDtoExtensions
{
    public static InfluenceDiagramDto DeepClone<InfluenceDiagramDto>(this InfluenceDiagramDto source)
    {
        var json = JsonSerializer.Serialize(source);
        return JsonSerializer.Deserialize<InfluenceDiagramDto>(json)!;
    }

    private static IssueOutgoingDto AddUtilityIssue(
        this InfluenceDiagramDto influenceDiagramDto,
        Guid utilityId,
        string name,
        params NodeOutgoingDto[] parentNodes)
    {
        var utilityNode = new NodeViaIssueOutgoingDto
        {
            Id = utilityId,
            IssueId = utilityId,
            ProjectId = influenceDiagramDto.projectId,
            Name = name,
        };
        var utilityIssue = new IssueOutgoingDto
        {
            Id = utilityId,
            ProjectId = influenceDiagramDto.projectId,
            Name = name,
            Type = IssueType.Utility.ToString(),
            Utility = new UtilityOutgoingDto
            {
                ProjectId = influenceDiagramDto.projectId,
                Id = utilityId,
                IssueId = utilityId,
            },
            Node = utilityNode
        };
        var utilityNodeWithIssue = new NodeOutgoingDto
        {
            Id = utilityId,
            IssueId = utilityId,
            ProjectId = influenceDiagramDto.projectId,
            Name = name,
            Issue = new IssueViaNodeOutgoingDto
            {
                Id = utilityId,
                ProjectId = influenceDiagramDto.projectId,
                Name = name,
                Type = IssueType.Utility.ToString(),
                Utility = utilityIssue.Utility,
            }
        };

        influenceDiagramDto.issues.Add(utilityIssue);
        foreach (var parentNode in parentNodes)
        {
            influenceDiagramDto.edges.Add(new EdgeOutgoingDto
            {
                Id = Guid.NewGuid(),
                ProjectId = influenceDiagramDto.projectId,
                TailIssueId = parentNode.IssueId,
                TailId = parentNode.Id,
                TailNode = parentNode,
                HeadIssueId = utilityId,
                HeadId = utilityId,
                HeadNode = utilityNodeWithIssue
            });
        }

        return utilityIssue;
    }

    private static void CreateRestrictedDiscreteUtilities(this InfluenceDiagramDto influenceDiagramDto, Guid restrictionTableId, EdgeOutgoingDto edge, string name)
    {
        var restrictionTable = influenceDiagramDto.restrictionTables.FirstOrDefault(rt => rt.Id == restrictionTableId);
        if (restrictionTable is null) return;

        influenceDiagramDto.AddUtilityIssue(restrictionTableId, name, edge.TailNode, edge.HeadNode);
        foreach (var entry in restrictionTable.RestrictionEntries)
        {
            if (!entry.IsChildUncertainty && entry.ParentStateId is not null && entry.ChildStateId is not null)
            {
                // The child of the entry is an option, meaning it is a parent of the discrete utility, but the parent can be either an option or an outcome, 
                // Check which one it is and add it to the appropriate list of parent ids
                var parentOutcomeIds = entry.IsParentUncertainty ? new List<Guid> { (Guid)entry.ParentStateId } : new List<Guid>();
                var parentOptionIds = entry.IsParentUncertainty ? new List<Guid>{(Guid)entry.ChildStateId} : new List<Guid> { (Guid)entry.ChildStateId, (Guid)entry.ParentStateId };
                // create a discrete utility for the restricted option given the parent state
                var discreteUtility = new DiscreteUtilityDto
                {
                    ProjectId = influenceDiagramDto.projectId,
                    UtilityId = restrictionTableId,
                    ParentOptionIds = parentOptionIds,
                    ParentOutcomeIds = parentOutcomeIds,
                    // using -1e100 instead of double.MinValue because the solver cannot handle extremely large negative values
                    UtilityValue = entry.RestrictionValue == 0 ? -1e100 : 0 
                };
                influenceDiagramDto.discreteUtilities.Add(discreteUtility);
            }
        }
    }
    
    public static void ApplyRestrictions(this InfluenceDiagramDto influenceDiagramDto)
    {
        RestrictDecisions(influenceDiagramDto);
        RestrictUncertainties(influenceDiagramDto);
    }

    private static void RestrictDecisions(InfluenceDiagramDto influenceDiagramDto)
    {
        // Get all restriction tables that apply to decisions and have at least one restriction entry with a value other than 1
        var restrictionTablesDecisions = influenceDiagramDto.restrictionTables
            .Where(rt => !rt.RestrictionEntries.All(re => re.IsChildUncertainty) &&
                rt.RestrictionEntries.Any(re => re.RestrictionValue != 1) // only apply restrictions if there are any entries with a restriction value other than 1
            )
            .ToList();
        var i = 0;
        foreach (var table in restrictionTablesDecisions)
        {
            // skip if all entries have a restriction value of 1, meaning no restrictions
            if (table.RestrictionEntries.All(re => re.RestrictionValue == 1)) continue;
            var edge = influenceDiagramDto.edges.First(e => e.Id == table.EdgeId);
            influenceDiagramDto.CreateRestrictedDiscreteUtilities(table.Id, edge, $"Restricted utility {i}");
            i++;
        }
    }

    private static void RestrictUncertainties(InfluenceDiagramDto influenceDiagramDto)
    {
        var discreteProbabilities = influenceDiagramDto.discreteProbabilities;
        // Get all restriction entries that apply to uncertainties and have a restriction value other than 1
        var restrictionEntriesUncertainties = influenceDiagramDto.restrictionTables
            .SelectMany(rt => rt.RestrictionEntries)
            .Where(re => re.IsChildUncertainty && re.RestrictionValue != 1) // only apply restrictions if there are any entries with a restriction value other than 1
            .ToList();
        foreach (var entry in restrictionEntriesUncertainties)
        {
            if (entry.IsChildUncertainty)
            {
                // child is an outcome, set the discrete probabilities that have that outcome/option as a parent to 0
                var affectedProbabilities = discreteProbabilities.Where(
                    dp => dp.OutcomeId == entry.ChildStateId &&
                    entry.ParentStateId is not null &&
                    (dp.ParentOptionIds.Contains((Guid)entry.ParentStateId) || dp.ParentOutcomeIds.Contains((Guid)entry.ParentStateId))).ToList();
                foreach (var probability in affectedProbabilities)
                {
                    probability.Probability = probability.Probability * entry.RestrictionValue;
                    // need to normalize the probabilities for the parent state after setting some to 0
                    // solver hanldes the case where all probabilities for a parent state are set to 0
                }
            }
        }
        NormalizeProbabilities(discreteProbabilities);
    }

    private static void NormalizeProbabilities(ICollection<DiscreteProbabilityDto> discreteProbabilities)
    {
        var probabilityRows = discreteProbabilities.GroupBy(dp =>
                    string.Join(",", dp.ParentOptionIds.OrderBy(x => x)
                        .Concat(dp.ParentOutcomeIds.OrderBy(x => x)))).ToList();
        foreach (var row in probabilityRows)
        {
            int precision = 2;
            var totalProbability = row.Sum(x => x.Probability);
            if (totalProbability is null || Math.Round(totalProbability.Value, precision) == 0 || Math.Round(totalProbability.Value, precision) == 1) continue; // no need to normalize 

            // normalize the probabilities for this row, but leave out any probabilities that are already 0
            // since they are restricted and should not be normalized
            var nonZeroProbabilities = row.Where(x => x.Probability > 0).ToList();
            var nonZeroTotalProbability = nonZeroProbabilities.Sum(x => x.Probability);
            foreach (var probability in nonZeroProbabilities)
            {
                probability.Probability = probability.Probability / nonZeroTotalProbability;
            }
        }
    }
}