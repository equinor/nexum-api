namespace PrismaApi.Infrastructure.Caching;

public static class CacheKeys
{
    public static string GetInfluenceDiagramKey(Guid projectId) => $"InfluenceDiagram_{projectId}";
    public static string GetIssuesInProjectKey(Guid projectId) => $"Issues_Project_{projectId}";
    public static string GetEdgesInProjectKey(Guid projectId) => $"Edges_Project_{projectId}";
    public static string GetNodesInProjectKey(Guid projectId) => $"Nodes_Project_{projectId}";
    public static string GetAssessmentKey(Guid projectId) => $"Assessment_Project_{projectId}";
    public static string GetObjectivesInProjectKey(Guid projectId) => $"Objectives_Project_{projectId}";
    public static string GetStrategyInProjectKey(Guid projectId) => $"Strategy_Project_{projectId}";
    public static string GetDiscreteProbabilitiesInProjectKey(Guid projectId) => $"DiscreteProbabilities_Project_{projectId}";
    public static string GetDiscreteUtilitiesInProjectKey(Guid projectId) => $"DiscreteUtilities_Project_{projectId}";
    public static string GetRestrictionTablesInProjectKey(Guid projectId) => $"RestrictionTables_Project_{projectId}";
    public static string GetBoardNodesInProjectKey(Guid projectId) => $"BoardNodes_Project_{projectId}";
    public static string GetBoardSheetsInProjectKey(Guid projectId) => $"BoardSheets_Project_{projectId}";
    public static string GetUserKey(string key) => $"user_{key.ToLower()}"; // id internal, name in public
    public static string GetProjectKey(Guid projectId) => $"Projects_{projectId}";
    public const string PublicProjectIdsKey = "Public_Project_Ids";
}
