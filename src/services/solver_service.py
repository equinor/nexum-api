import uuid
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from src.constants import Type
from src.session_manager import sessionmanager
from src.services.pyagrum_solver import (
    PyagrumSolver, 
    SolutionDto, 
    OptimalOption,
)
from src.services.scenario_service import ScenarioService
from src.services.decision_tree.decision_tree_creator import (
    DecisionTreeCreator, 
    DecisionTreeDTO, 
    EndPointNodeDto, 
    ProbabilityDto,
)
from src.dtos.outcome_dtos import OutcomeOutgoingDto
from src.dtos.model_solution_dtos import SolutionDto



executor = ThreadPoolExecutor()


class SolverService:
    def __init__(
        self,
        scenario_service: ScenarioService,
    ):
        self.scenario_service = scenario_service

    async def find_optimal_decision_pyagrum(self, scenario_id: uuid.UUID):
        async for session in sessionmanager.get_session():
            (
                issues,
                edges,
            ) = await self.scenario_service.get_influence_diagram_data(session, scenario_id)

        solution = await PyagrumSolver().find_optimal_decisions(issues=issues, edges=edges)

        return solution
    
    async def get_decision_tree_for_optimal_decisions(self, scenario_id: uuid.UUID):
        async for session in sessionmanager.get_session():
            (
                issues,
                edges,
            ) = await self.scenario_service.get_influence_diagram_data(session, scenario_id)

        solution = await PyagrumSolver().find_optimal_decisions(issues=issues, edges=edges)

        decision_tree_creator = await DecisionTreeCreator.initialize(scenario_id, nodes = issues, edges = edges)
        DT_partial_order = await decision_tree_creator.calculate_partial_order()
        decision_tree = await decision_tree_creator.convert_to_decision_tree(scenario_id=issues[0].scenario_id, partial_order=DT_partial_order)
        pruning_class = DecisionTreeRecusivePruning()
        dt_dtos = await decision_tree.to_issue_dtos()
        return pruning_class.rec(dt_dtos, solution)

class DecisionTreeRecusivePruning:
    current_path: set[uuid.UUID] = set()

    def _parents_check(self, decision: OptimalOption) -> bool:
        parent_ids = [x.state.id for x in decision.parent_states]
        # check that all parent ids are in current path
        # parent ids are a subset of current path is still valid
        if set(parent_ids).issubset(self.current_path):
            return True
        return False 
    
    def _handle_decision_node(self, current_node: DecisionTreeDTO, solution: SolutionDto ):
        optimal_decisions = solution.get_all_optimal_decisions()
        decision_state_id = None
        correct_option_index: Optional[int] = None
        
        # find the solution for the decision node given the current path
        for decision in optimal_decisions:
            decision.parent_states
            if decision.decision_id == current_node.tree_node.issue.id and self._parents_check(decision):
                decision_state_id = decision.state.id
                self.current_path.add(decision.state.id) # path for decision
                correct_option_index = [x.id for x in current_node.tree_node.issue.decision.options].index(decision.state.id)
                break
        if correct_option_index is None:
            raise Exception(f"solution for decision node {current_node.tree_node.issue.name} not found")
        # prune tree to remove none optimal paths
        current_node.children = [current_node.children[correct_option_index]]
        current_node.tree_node.issue.decision.options = [
            option 
            for option in current_node.tree_node.issue.decision.options 
            if option.id == decision_state_id
        ]
        # recursion call
        self.rec(current_node.children[0], solution)
        if decision_state_id:
            self.current_path.remove(decision_state_id)
        return current_node
    
    def _handle_uncertainty_node(self, current_node: DecisionTreeDTO, solution: SolutionDto):
        if (
            current_node.tree_node.issue.uncertainty is None 
            or current_node.tree_node.issue.uncertainty.outcomes.__len__() == 0
            or current_node.children is None
            or current_node.tree_node.probabilities is None
        ):
                raise Exception("Invalid decision tree path")
        # sort the probabilities to match the order of outcomes
        outcome_order = {outcome.id: i for i, outcome in enumerate(current_node.tree_node.issue.uncertainty.outcomes)}
        current_node.tree_node.probabilities.sort(key=lambda prob: outcome_order.get(prob.outcome_id, float('inf')))

        child: DecisionTreeDTO
        prob: ProbabilityDto
        outcome: OutcomeOutgoingDto
        for child, prob, outcome in zip(
            current_node.children, 
            current_node.tree_node.probabilities, 
            current_node.tree_node.issue.uncertainty.outcomes
        ):
            if prob.probability_value == 0:
                current_node.tree_node.issue.uncertainty.outcomes.remove(outcome)
                current_node.tree_node.probabilities.remove(prob)
                current_node.children.remove(child)
            
        for child, prob, outcome in zip(
            current_node.children, 
            current_node.tree_node.probabilities, 
            current_node.tree_node.issue.uncertainty.outcomes
        ):
            self.current_path.add(outcome.id) # path for uncertainty
            # recursion call
            self.rec(child, solution)
            self.current_path.remove(outcome.id)
        return current_node

    def rec(self, current_node: DecisionTreeDTO, solution: SolutionDto) -> Optional[DecisionTreeDTO]:
        # if end node return
        if isinstance(current_node.tree_node.issue, EndPointNodeDto):
            return
        # Decision node
        if current_node.tree_node.issue.type == Type.DECISION.value and current_node.tree_node.issue. decision is not None and current_node.children:
            current_node = self._handle_decision_node(current_node, solution)
            
        # uncertainty node
        else:
            current_node = self._handle_uncertainty_node(current_node, solution)
        return current_node
    