using Microsoft.Extensions.DependencyInjection;
using PrismaApi.Domain.Constants;
using PrismaApi.Domain.Entities;
using PrismaApi.Infrastructure.Context;
using PrismaApi.Test.Fixture;

namespace PrismaApi.Test.Data;

public class TestModelBuilder
{
    static Issue BuildIssue(Guid issueId, Guid projectId, string name, string type, string boundary, int order, string userId) =>
        new()
        {
            Id = issueId,
            ProjectId = projectId,
            Type = type,
            Boundary = boundary,
            Name = name,
            Description = $"{name} description",
            Order = order,
            CreatedById = userId,
            UpdatedById = userId
        };

    static Node BuildNode(Guid issueId, Guid projectId, string name) =>
        new()
        {
            Id = issueId,
            ProjectId = projectId,
            IssueId = issueId,
            Name = name
        };

    static NodeStyle BuildNodeStyle(Guid nodeId, double xPosition, double yPosition) =>
        new()
        {
            Id = nodeId,
            NodeId = nodeId,
            XPosition = xPosition,
            YPosition = yPosition
        };
    internal static async Task<TestArguments> BuildFreshTestDataAsync(PrismaApiFixture fixture)
    {
        using var scope = fixture.ApiFactory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var anyDataFound = db.Projects.Any();
        var args = new TestArguments();

        var primaryUser = new User
        {
            Id = fixture.PrismaUser.Id!,
            Name = fixture.PrismaUser.Name!
        };
        var secondaryUser = new User
        {
            Id = fixture.SecondaryUser.Id!,
            Name = fixture.SecondaryUser.Name!
        };
        if (!anyDataFound)
        {
            db.Users.AddRange(primaryUser, secondaryUser);
        }

        if (!db.ValueMetrics.Any(vm => vm.Id == DomainConstants.DefaultValueMetricId))
        {
            db.ValueMetrics.Add(new ValueMetric
            {
                Id = DomainConstants.DefaultValueMetricId,
                Name = DomainConstants.DefaultValueMetricName
            });
        }

        var primaryProject = new Project
        {
            Id = args.TestProjectId,
            Name = "Test Project",
            CreatedById = primaryUser.Id,
            UpdatedById = primaryUser.Id,
        };
        var secondaryProject = new Project
        {
            Id = args.SecondaryProjectId,
            Name = "Test Project - Larger",
            CreatedById = secondaryUser.Id,
            UpdatedById = secondaryUser.Id,
        };

        db.Projects.AddRange(primaryProject, secondaryProject);

        db.ProjectRoles.AddRange(
            new ProjectRole
            {
                Id = Guid.NewGuid(),
                ProjectId = primaryProject.Id,
                UserId = primaryUser.Id,
                Role = ProjectRoleType.Facilitator.ToString(),
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            },
            new ProjectRole
            {
                Id = Guid.NewGuid(),
                ProjectId = secondaryProject.Id,
                UserId = secondaryUser.Id,
                Role = ProjectRoleType.Member.ToString(),
                CreatedById = secondaryUser.Id,
                UpdatedById = secondaryUser.Id
            });

        var primaryDecision1Id = args.DecisionIssueId;
        var primaryUncertainty1Id = args.UncertaintyIssueId;
        var primaryDecision2Id = args.DecisionIssue2Id;
        var primaryUncertainty2Id = args.UncertaintyIssue2Id;
        var issueDeleteId = args.IssueDeleteId;
        var issueBulkDeleteId = args.IssueBulkDeleteId;
        var decisionDeleteIssueId = args.DecisionDeleteIssueId;
        var decisionBulkDeleteIssueId = args.DecisionBulkDeleteIssueId;
        var uncertaintyDeleteIssueId = args.UncertaintyDeleteIssueId;
        var uncertaintyBulkDeleteIssueId = args.UncertaintyBulkDeleteIssueId;
        var utilityIssueId = args.UtilityIssueId;

        var primaryDecision1Issue = BuildIssue(primaryDecision1Id, primaryProject.Id, "Primary Decision 1", IssueType.Decision.ToString(), Boundary.On.ToString(), 0, primaryUser.Id);
        var primaryUncertainty1Issue = BuildIssue(primaryUncertainty1Id, primaryProject.Id, "Primary Uncertainty 1", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 1, primaryUser.Id);
        var primaryDecision2Issue = BuildIssue(primaryDecision2Id, primaryProject.Id, "Primary Decision 2", IssueType.Decision.ToString(), Boundary.On.ToString(), 2, primaryUser.Id);
        var primaryUncertainty2Issue = BuildIssue(primaryUncertainty2Id, primaryProject.Id, "Primary Uncertainty 2", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 3, primaryUser.Id);
        var issueDelete = BuildIssue(issueDeleteId, primaryProject.Id, "Delete Issue", IssueType.Decision.ToString(), Boundary.On.ToString(), 4, primaryUser.Id);
        var issueBulkDelete = BuildIssue(issueBulkDeleteId, primaryProject.Id, "Bulk Delete Issue", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 5, primaryUser.Id);
        var decisionDeleteIssue = BuildIssue(decisionDeleteIssueId, primaryProject.Id, "Delete Decision Issue", IssueType.Decision.ToString(), Boundary.On.ToString(), 6, primaryUser.Id);
        var decisionBulkDeleteIssue = BuildIssue(decisionBulkDeleteIssueId, primaryProject.Id, "Bulk Delete Decision Issue", IssueType.Decision.ToString(), Boundary.On.ToString(), 7, primaryUser.Id);
        var uncertaintyDeleteIssue = BuildIssue(uncertaintyDeleteIssueId, primaryProject.Id, "Delete Uncertainty Issue", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 8, primaryUser.Id);
        var uncertaintyBulkDeleteIssue = BuildIssue(uncertaintyBulkDeleteIssueId, primaryProject.Id, "Bulk Delete Uncertainty Issue", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 9, primaryUser.Id);
        var utilityIssue = BuildIssue(utilityIssueId, primaryProject.Id, "Utility Issue", IssueType.Utility.ToString(), Boundary.In.ToString(), 10, primaryUser.Id);

        db.Issues.AddRange(
            primaryDecision1Issue,
            primaryUncertainty1Issue,
            primaryDecision2Issue,
            primaryUncertainty2Issue,
            issueDelete,
            issueBulkDelete,
            decisionDeleteIssue,
            decisionBulkDeleteIssue,
            uncertaintyDeleteIssue,
            uncertaintyBulkDeleteIssue,
            utilityIssue);
        db.Nodes.AddRange(
            BuildNode(primaryDecision1Id, primaryProject.Id, primaryDecision1Issue.Name),
            BuildNode(primaryUncertainty1Id, primaryProject.Id, primaryUncertainty1Issue.Name),
            BuildNode(primaryDecision2Id, primaryProject.Id, primaryDecision2Issue.Name),
            BuildNode(primaryUncertainty2Id, primaryProject.Id, primaryUncertainty2Issue.Name),
            BuildNode(issueDeleteId, primaryProject.Id, issueDelete.Name),
            BuildNode(issueBulkDeleteId, primaryProject.Id, issueBulkDelete.Name),
            BuildNode(decisionDeleteIssueId, primaryProject.Id, decisionDeleteIssue.Name),
            BuildNode(decisionBulkDeleteIssueId, primaryProject.Id, decisionBulkDeleteIssue.Name),
            BuildNode(uncertaintyDeleteIssueId, primaryProject.Id, uncertaintyDeleteIssue.Name),
            BuildNode(uncertaintyBulkDeleteIssueId, primaryProject.Id, uncertaintyBulkDeleteIssue.Name),
            BuildNode(utilityIssueId, primaryProject.Id, utilityIssue.Name));
        db.NodeStyles.AddRange(
            BuildNodeStyle(primaryDecision1Id, 0, 0),
            BuildNodeStyle(primaryUncertainty1Id, 150, 0),
            BuildNodeStyle(primaryDecision2Id, 300, 0),
            BuildNodeStyle(primaryUncertainty2Id, 450, 0),
            BuildNodeStyle(issueDeleteId, 600, 0),
            BuildNodeStyle(issueBulkDeleteId, 750, 0),
            BuildNodeStyle(decisionDeleteIssueId, 900, 0),
            BuildNodeStyle(decisionBulkDeleteIssueId, 1050, 0),
            BuildNodeStyle(uncertaintyDeleteIssueId, 1200, 0),
            BuildNodeStyle(uncertaintyBulkDeleteIssueId, 1350, 0),
            BuildNodeStyle(utilityIssueId, 1500, 0));
        db.Decisions.AddRange(
            new Decision { Id = primaryDecision1Id, IssueId = primaryDecision1Id, ProjectId = primaryProject.Id, Type = IssueType.Decision.ToString() },
            new Decision { Id = primaryDecision2Id, IssueId = primaryDecision2Id, ProjectId = primaryProject.Id, Type = IssueType.Decision.ToString() },
            new Decision { Id = issueDeleteId, IssueId = issueDeleteId, ProjectId = primaryProject.Id, Type = IssueType.Decision.ToString() },
            new Decision { Id = decisionDeleteIssueId, IssueId = decisionDeleteIssueId, ProjectId = primaryProject.Id, Type = IssueType.Decision.ToString() },
            new Decision { Id = decisionBulkDeleteIssueId, IssueId = decisionBulkDeleteIssueId, ProjectId = primaryProject.Id, Type = IssueType.Decision.ToString() });
        db.Uncertainties.AddRange(
            new Uncertainty { Id = primaryUncertainty1Id, IssueId = primaryUncertainty1Id, ProjectId = primaryProject.Id, IsKey = true },
            new Uncertainty { Id = primaryUncertainty2Id, IssueId = primaryUncertainty2Id, ProjectId = primaryProject.Id, IsKey = true },
            new Uncertainty { Id = issueBulkDeleteId, IssueId = issueBulkDeleteId, ProjectId = primaryProject.Id, IsKey = true },
            new Uncertainty { Id = uncertaintyDeleteIssueId, IssueId = uncertaintyDeleteIssueId, ProjectId = primaryProject.Id, IsKey = true },
            new Uncertainty { Id = uncertaintyBulkDeleteIssueId, IssueId = uncertaintyBulkDeleteIssueId, ProjectId = primaryProject.Id, IsKey = true });
        db.Edges.AddRange(
            new Edge { Id = args.EdgeId, ProjectId = primaryProject.Id, TailId = primaryDecision1Id, HeadId = primaryUncertainty1Id },
            new Edge { Id = Guid.NewGuid(), ProjectId = primaryProject.Id, TailId = primaryUncertainty1Id, HeadId = primaryDecision2Id },
            new Edge { Id = Guid.NewGuid(), ProjectId = primaryProject.Id, TailId = primaryDecision2Id, HeadId = primaryUncertainty2Id },
            new Edge { Id = args.EdgeDeleteId, ProjectId = primaryProject.Id, TailId = primaryUncertainty1Id, HeadId = primaryDecision2Id },
            new Edge { Id = args.EdgeBulkDeleteId, ProjectId = primaryProject.Id, TailId = primaryDecision2Id, HeadId = primaryUncertainty2Id });

        db.Utilities.Add(new Utility { Id = utilityIssueId, IssueId = utilityIssueId, ProjectId = primaryProject.Id });

        db.Options.AddRange(
            new Option { Id = args.OptionId, DecisionId = primaryDecision1Id, ProjectId = primaryProject.Id, Name = "Primary Option", Utility = 1.1 },
            new Option { Id = args.OptionDeleteId, DecisionId = primaryDecision1Id, ProjectId = primaryProject.Id, Name = "Delete Option", Utility = 2.2 },
            new Option { Id = args.OptionBulkDeleteId, DecisionId = primaryDecision1Id, ProjectId = primaryProject.Id, Name = "Bulk Delete Option", Utility = 2.3 });

        db.Outcomes.AddRange(
            new Outcome { Id = args.OutcomeId, UncertaintyId = primaryUncertainty1Id, ProjectId = primaryProject.Id, Name = "Primary Outcome", Utility = 3.3 },
            new Outcome { Id = args.OutcomeDeleteId, UncertaintyId = primaryUncertainty1Id, ProjectId = primaryProject.Id, Name = "Delete Outcome", Utility = 4.4 },
            new Outcome { Id = args.OutcomeBulkDeleteId, UncertaintyId = primaryUncertainty1Id, ProjectId = primaryProject.Id, Name = "Bulk Delete Outcome", Utility = 4.5 });

        db.Objectives.AddRange(
            new Objective
            {
                Id = args.ObjectiveId,
                ProjectId = primaryProject.Id,
                Name = "Primary Objective",
                Description = "Primary objective description",
                Type = ObjectiveType.Fundamental.ToString(),
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            },
            new Objective
            {
                Id = args.ObjectiveDeleteId,
                ProjectId = primaryProject.Id,
                Name = "Delete Objective",
                Description = "Delete objective description",
                Type = ObjectiveType.Strategic.ToString(),
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            },
            new Objective
            {
                Id = args.ObjectiveBulkDeleteId,
                ProjectId = primaryProject.Id,
                Name = "Bulk Delete Objective",
                Description = "Bulk delete objective description",
                Type = ObjectiveType.Strategic.ToString(),
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            });

        db.Strategies.AddRange(
            new Strategy
            {
                Id = args.StrategyId,
                ProjectId = primaryProject.Id,
                Name = "Primary Strategy",
                Description = "Primary strategy description",
                Rationale = "Primary strategy rationale",
                Icon = "icon-primary",
                IconColor = "#111111",
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            },
            new Strategy
            {
                Id = args.StrategyDeleteId,
                ProjectId = primaryProject.Id,
                Name = "Delete Strategy",
                Description = "Delete strategy description",
                Rationale = "Delete strategy rationale",
                Icon = "icon-delete",
                IconColor = "#222222",
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            },
            new Strategy
            {
                Id = args.StrategyBulkDeleteId,
                ProjectId = primaryProject.Id,
                Name = "Bulk Delete Strategy",
                Description = "Bulk delete strategy description",
                Rationale = "Bulk delete strategy rationale",
                Icon = "icon-bulk",
                IconColor = "#333333",
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            });

        db.StrategyOptions.AddRange(
            new StrategyOption { StrategyId = args.StrategyId, OptionId = args.OptionId, ProjectId = primaryProject.Id },
            new StrategyOption { StrategyId = args.StrategyDeleteId, OptionId = args.OptionDeleteId, ProjectId = primaryProject.Id },
            new StrategyOption { StrategyId = args.StrategyBulkDeleteId, OptionId = args.OptionBulkDeleteId, ProjectId = primaryProject.Id });

        db.DiscreteUtilities.AddRange(
            new DiscreteUtility
            {
                Id = args.DiscreteUtilityId,
                UtilityId = utilityIssueId,
                ValueMetricId = DomainConstants.DefaultValueMetricId,
                ProjectId = primaryProject.Id,
                UtilityValue = 3.14
            },
            new DiscreteUtility
            {
                Id = args.DiscreteUtilityDeleteId,
                UtilityId = utilityIssueId,
                ValueMetricId = DomainConstants.DefaultValueMetricId,
                ProjectId = primaryProject.Id,
                UtilityValue = 2.71
            },
            new DiscreteUtility
            {
                Id = args.DiscreteUtilityBulkDeleteId,
                UtilityId = utilityIssueId,
                ValueMetricId = DomainConstants.DefaultValueMetricId,
                ProjectId = primaryProject.Id,
                UtilityValue = 2.72
            });

        var secondaryDecision1Id = Guid.NewGuid();
        var secondaryUncertainty1Id = Guid.NewGuid();
        var secondaryDecision2Id = Guid.NewGuid();
        var secondaryUncertainty2Id = Guid.NewGuid();
        var secondaryDecision3Id = Guid.NewGuid();
        var secondaryUncertainty3Id = Guid.NewGuid();

        var secondaryDecision1Issue = BuildIssue(secondaryDecision1Id, secondaryProject.Id, "Secondary Decision 1", IssueType.Decision.ToString(), Boundary.On.ToString(), 0, secondaryUser.Id);
        var secondaryUncertainty1Issue = BuildIssue(secondaryUncertainty1Id, secondaryProject.Id, "Secondary Uncertainty 1", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 1, secondaryUser.Id);
        var secondaryDecision2Issue = BuildIssue(secondaryDecision2Id, secondaryProject.Id, "Secondary Decision 2", IssueType.Decision.ToString(), Boundary.On.ToString(), 2, secondaryUser.Id);
        var secondaryUncertainty2Issue = BuildIssue(secondaryUncertainty2Id, secondaryProject.Id, "Secondary Uncertainty 2", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 3, secondaryUser.Id);
        var secondaryDecision3Issue = BuildIssue(secondaryDecision3Id, secondaryProject.Id, "Secondary Decision 3", IssueType.Decision.ToString(), Boundary.On.ToString(), 4, secondaryUser.Id);
        var secondaryUncertainty3Issue = BuildIssue(secondaryUncertainty3Id, secondaryProject.Id, "Secondary Uncertainty 3", IssueType.Uncertainty.ToString(), Boundary.In.ToString(), 5, secondaryUser.Id);

        db.Issues.AddRange(
            secondaryDecision1Issue,
            secondaryUncertainty1Issue,
            secondaryDecision2Issue,
            secondaryUncertainty2Issue,
            secondaryDecision3Issue,
            secondaryUncertainty3Issue);
        db.Nodes.AddRange(
            BuildNode(secondaryDecision1Id, secondaryProject.Id, secondaryDecision1Issue.Name),
            BuildNode(secondaryUncertainty1Id, secondaryProject.Id, secondaryUncertainty1Issue.Name),
            BuildNode(secondaryDecision2Id, secondaryProject.Id, secondaryDecision2Issue.Name),
            BuildNode(secondaryUncertainty2Id, secondaryProject.Id, secondaryUncertainty2Issue.Name),
            BuildNode(secondaryDecision3Id, secondaryProject.Id, secondaryDecision3Issue.Name),
            BuildNode(secondaryUncertainty3Id, secondaryProject.Id, secondaryUncertainty3Issue.Name));
        db.NodeStyles.AddRange(
            BuildNodeStyle(secondaryDecision1Id, 0, 120),
            BuildNodeStyle(secondaryUncertainty1Id, 150, 120),
            BuildNodeStyle(secondaryDecision2Id, 300, 120),
            BuildNodeStyle(secondaryUncertainty2Id, 450, 120),
            BuildNodeStyle(secondaryDecision3Id, 600, 120),
            BuildNodeStyle(secondaryUncertainty3Id, 750, 120));
        db.Decisions.AddRange(
            new Decision { Id = secondaryDecision1Id, IssueId = secondaryDecision1Id, ProjectId = secondaryProject.Id, Type = IssueType.Decision.ToString() },
            new Decision { Id = secondaryDecision2Id, IssueId = secondaryDecision2Id, ProjectId = secondaryProject.Id, Type = IssueType.Decision.ToString() },
            new Decision { Id = secondaryDecision3Id, IssueId = secondaryDecision3Id, ProjectId = secondaryProject.Id, Type = IssueType.Decision.ToString() });
        db.Uncertainties.AddRange(
            new Uncertainty { Id = secondaryUncertainty1Id, IssueId = secondaryUncertainty1Id, ProjectId = secondaryProject.Id, IsKey = true },
            new Uncertainty { Id = secondaryUncertainty2Id, IssueId = secondaryUncertainty2Id, ProjectId = secondaryProject.Id, IsKey = true },
            new Uncertainty { Id = secondaryUncertainty3Id, IssueId = secondaryUncertainty3Id, ProjectId = secondaryProject.Id, IsKey = true });
        db.Edges.AddRange(
            new Edge { Id = Guid.NewGuid(), ProjectId = secondaryProject.Id, TailId = secondaryDecision1Id, HeadId = secondaryUncertainty1Id },
            new Edge { Id = Guid.NewGuid(), ProjectId = secondaryProject.Id, TailId = secondaryUncertainty1Id, HeadId = secondaryDecision2Id },
            new Edge { Id = Guid.NewGuid(), ProjectId = secondaryProject.Id, TailId = secondaryDecision2Id, HeadId = secondaryUncertainty2Id },
            new Edge { Id = Guid.NewGuid(), ProjectId = secondaryProject.Id, TailId = secondaryUncertainty2Id, HeadId = secondaryDecision3Id },
            new Edge { Id = Guid.NewGuid(), ProjectId = secondaryProject.Id, TailId = secondaryDecision3Id, HeadId = secondaryUncertainty3Id });

        db.BoardSheets.AddRange(
            new BoardSheet
            {
                Id = args.BoardSheetId,
                ProjectId = primaryProject.Id,
                Name = "Primary Board Sheet",
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            },
            new BoardSheet
            {
                Id = args.BoardSheetDeleteId,
                ProjectId = primaryProject.Id,
                Name = "Delete Board Sheet",
                CreatedById = primaryUser.Id,
                UpdatedById = primaryUser.Id
            });

        await db.SaveChangesAsync();
        return args;
    }
}

public class TestArguments
{

    public Guid TestProjectId { get; set; } = Guid.NewGuid();
    public Guid SecondaryProjectId { get; set; } = Guid.NewGuid();
    public string SecondaryUserId { get; set; } = string.Empty;
    public Guid DecisionIssueId { get; set; } = Guid.NewGuid();
    public Guid UncertaintyIssueId { get; set; } = Guid.NewGuid();
    public Guid DecisionIssue2Id { get; set; } = Guid.NewGuid();
    public Guid UncertaintyIssue2Id { get; set; } = Guid.NewGuid();
    public Guid IssueDeleteId { get; set; } = Guid.NewGuid();
    public Guid IssueBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid DecisionDeleteIssueId { get; set; } = Guid.NewGuid();
    public Guid DecisionBulkDeleteIssueId { get; set; } = Guid.NewGuid();
    public Guid UncertaintyDeleteIssueId { get; set; } = Guid.NewGuid();
    public Guid UncertaintyBulkDeleteIssueId { get; set; } = Guid.NewGuid();
    public Guid UtilityIssueId { get; set; } = Guid.NewGuid();
    public Guid OptionId { get; set; } = Guid.NewGuid();
    public Guid OptionDeleteId { get; set; } = Guid.NewGuid();
    public Guid OptionBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid OutcomeId { get; set; } = Guid.NewGuid();
    public Guid OutcomeDeleteId { get; set; } = Guid.NewGuid();
    public Guid OutcomeBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid ObjectiveId { get; set; } = Guid.NewGuid();
    public Guid ObjectiveDeleteId { get; set; } = Guid.NewGuid();
    public Guid ObjectiveBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid StrategyId { get; set; } = Guid.NewGuid();
    public Guid StrategyDeleteId { get; set; } = Guid.NewGuid();
    public Guid StrategyBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid DiscreteUtilityId { get; set; } = Guid.NewGuid();
    public Guid DiscreteUtilityDeleteId { get; set; } = Guid.NewGuid();
    public Guid DiscreteUtilityBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid EdgeId { get; set; } = Guid.NewGuid();
    public Guid EdgeDeleteId { get; set; } = Guid.NewGuid();
    public Guid EdgeBulkDeleteId { get; set; } = Guid.NewGuid();
    public Guid BoardSheetId { get; set; } = Guid.NewGuid();
    public Guid BoardSheetDeleteId { get; set; } = Guid.NewGuid();

    public static int GenerateUniqueId()
    {
        var ticks = DateTime.UtcNow.Ticks;
        var randomNumber = new Random().Next();
        return (int)((ticks / TimeSpan.TicksPerSecond) ^ randomNumber);
    }
}
