import uuid
from concurrent.futures import ThreadPoolExecutor
from src.session_manager import sessionmanager
from src.services.pyagrum_solver import PyagrumSolver
from src.services.project_service import ProjectService
from src.services.decision_tree.decision_tree_creator import DecisionTreeCreator
from src.services.decision_tree_pruning_service import DecisionTreePruningService, OptimalDecisionTreePruner

executor = ThreadPoolExecutor()

class SolverService:
    def __init__(
        self,
        project_service: ProjectService,
    ):
        self.project_service = project_service

    async def find_optimal_decision_pyagrum(self, project_id: uuid.UUID):
        async for session in sessionmanager.get_session():
            (
                issues,
                edges,
            ) = await self.project_service.get_influence_diagram_data(session, project_id)

        solution = await PyagrumSolver().find_optimal_decisions(issues=issues, edges=edges)

        return solution
    
    async def get_decision_tree_for_optimal_decisions(self, project_id: uuid.UUID):
        async for session in sessionmanager.get_session():
            (
                issues,
                edges,
            ) = await self.project_service.get_influence_diagram_data(session, project_id)

        solution = await PyagrumSolver().find_optimal_decisions(issues=issues, edges=edges)

        decision_tree_creator = await DecisionTreeCreator.initialize(project_id, nodes = issues, edges = edges)
        DT_partial_order = await decision_tree_creator.calculate_partial_order()
        decision_tree = await decision_tree_creator.convert_to_decision_tree(project_id=issues[0].project_id, partial_order=DT_partial_order)

        dt_dtos = await decision_tree.to_issue_dtos()

        pruning_service = DecisionTreePruningService(pruner=OptimalDecisionTreePruner())
        return pruning_service.prune_tree_for_optimal_decisions(dt_dtos, solution)
