import uuid
import pyagrum as gum # type: ignore
from itertools import product
from src.constants import Type
from src.utils.discrete_probability_array_manager import DiscreteProbabilityArrayManager
from src.dtos.issue_dtos import IssueOutgoingDto
from src.dtos.edge_dtos import EdgeOutgoingDto
from src.dtos.option_dtos import OptionOutgoingDto
from src.dtos.outcome_dtos import OutcomeOutgoingDto
from src.dtos.model_solution_dtos import (
    ParentState,
    OptimalOption,
    DecisionSolution,
    SolutionDto,
)
from src.services.decision_tree.decision_tree_creator import DecisionTreeCreator
from typing import TypeVar, Optional

T = TypeVar('T', OptionOutgoingDto, OutcomeOutgoingDto)

# run for each optimal solution

class PyagrumSolver:
    def __init__(self):
        self.node_lookup: dict[str, int] = {}
        self.diagram = gum.InfluenceDiagram()
        self.issues: list[IssueOutgoingDto] = []
        self.edges: list[EdgeOutgoingDto] = []

    def _reset_diagram(self):
        self.diagram = gum.InfluenceDiagram()

    def add_to_lookup(self, issue: IssueOutgoingDto, node_id: int) -> None:
        self.node_lookup[issue.id.__str__()] = node_id

    def build_influence_diagram(self, issues: list[IssueOutgoingDto], edges: list[EdgeOutgoingDto]):
        self.issues = issues
        self.edges = edges
        self.add_nodes(issues)
        self.add_edges(edges)
        self.fill_cpts(issues)
        self.add_virtual_utilities(issues)
        self.fill_utilities(issues)

    def _sort_state_dtos(self, dtos: list[T]) -> list[T]:
        return sorted(dtos, key=lambda x: x.id.__str__())
    
    def _find_state(self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None) -> OptionOutgoingDto|OutcomeOutgoingDto:
        """Returns the option/outcome that matches the state id. Looks through the issues variable if included, otherwise looks through all issues in the model."""
        states: list[OptionOutgoingDto|OutcomeOutgoingDto] = []
        if issues:
            [states.extend(issue.decision.options) for issue in issues if issue.decision is not None]
            [states.extend(issue.uncertainty.outcomes) for issue in issues if issue.uncertainty is not None]    
        else:
            [states.extend(issue.decision.options) for issue in self.issues if issue.decision is not None]
            [states.extend(issue.uncertainty.outcomes) for issue in self.issues if issue.uncertainty is not None]    
        
        return [state for state in states if str(state.id) == state_id][0]
    
    def _find_state_decision(self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None) -> OptionOutgoingDto:
        """Returns the option that matches the state id. Looks through the issues variable if included, otherwise looks through all issues in the model."""
        states: list[OptionOutgoingDto] = []
        if issues:
            [states.extend(issue.decision.options) for issue in issues if issue.decision is not None]
        else:
            [states.extend(issue.decision.options) for issue in self.issues if issue.decision is not None]
        
        return [state for state in states if str(state.id) == state_id][0]
    
    def _find_state_uncertainty(self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None) -> OutcomeOutgoingDto:
        """Returns the outcome that matches the state id. Looks through the issues variable if included, otherwise looks through all issues in the model."""
        states: list[OutcomeOutgoingDto] = []
        if issues:
            [states.extend(issue.uncertainty.outcomes) for issue in issues if issue.uncertainty is not None]    
        else:
            [states.extend(issue.uncertainty.outcomes) for issue in self.issues if issue.uncertainty is not None]    
        
        return [state for state in states if str(state.id) == state_id][0]

    def _pyagrum_optimal_decision_argmax(self, ie: gum.ShaferShenoyLIMIDInference, decision_issue_id: str) -> list[dict[str, int]]:
        return ie.optimalDecision(decision_issue_id).argmax()[0] # type: ignore
    
    def _pyagrum_get_mean_utility(self, ie: gum.ShaferShenoyLIMIDInference, node_name: str) -> float:
        return ie.meanVar(node_name)["mean"] # type: ignore
    
    def _pyagrum_get_node_labels(self, node_identifier: str|int) -> tuple[str]:
        return self.diagram.variable(node_identifier).labels() # type: ignore
    
    def get_optimal_decisions(self, ie: gum.ShaferShenoyLIMIDInference, decision_issue_id: str):
        pyagrum_result: list[dict[str, int]] = self._pyagrum_optimal_decision_argmax(ie, decision_issue_id)
        optimal_decisions: list[OptimalOption] = []
        for result in pyagrum_result:
            optimal_state: OptionOutgoingDto = self._find_state_decision(self._pyagrum_get_node_labels(decision_issue_id)[result[decision_issue_id]])
            parent_states: list[ParentState] = []

            for i, key in enumerate(result):
                # skip the decision in question
                if i == 0:
                    continue
                parent_state_id: str = self._pyagrum_get_node_labels(key)[result[key]]
                parent_state = self._find_state(parent_state_id)
                parent_states.append(ParentState(parent_id=uuid.UUID(key), state=parent_state))

            optimal_decisions.append(OptimalOption(parent_states=parent_states,decision_id=uuid.UUID(decision_issue_id), state= optimal_state))

        return DecisionSolution(optimal_decisions=optimal_decisions, mean=self._pyagrum_get_mean_utility(ie, decision_issue_id))

    def get_solution(self, ie: gum.ShaferShenoyLIMIDInference, decisions: list[str]) -> SolutionDto:
        return SolutionDto(decision_solutions=[self.get_optimal_decisions(ie, x) for x in decisions])

    async def find_optimal_decisions(self, issues: list[IssueOutgoingDto], edges: list[EdgeOutgoingDto]) -> SolutionDto:
        self.build_influence_diagram(issues, edges)

        decision_tree_creator = await DecisionTreeCreator.initialize(project_id = issues[0].project_id,
            nodes = issues,
            edges = edges
        )
        
        partial_order = await decision_tree_creator.calculate_partial_order()

        partial_order = [
            (await decision_tree_creator.get_node_from_uuid(tree_node_id))
            for tree_node_id in partial_order
        ]

        partial_order = [
            tree_node.issue.id
            for tree_node in partial_order if tree_node is not None
        ]

        partial_order_decisions = [x for x in partial_order if x in [issue.id for issue in issues if issue.type == Type.DECISION.value]]
        ie = gum.ShaferShenoyLIMIDInference(self.diagram)

        ie.addNoForgettingAssumption([str(x) for x in partial_order_decisions]) # type: ignore

        if not ie.isSolvable():
            raise RuntimeError("Influence diagram is not solvable")
        ie.makeInference()

        solution =  self.get_solution(ie, [str(x) for x in partial_order_decisions])

        return solution

    def add_node(self, issue: IssueOutgoingDto):
        if issue.type == Type.DECISION:
            assert issue.decision is not None
            node_id = self.diagram.addDecisionNode( # type: ignore
                gum.LabelizedVariable(
                    issue.id.__str__(),
                    issue.description,
                    sorted([option.id.__str__() for option in issue.decision.options]),
                )
            )
            self.add_to_lookup(issue, node_id)

        if issue.type == Type.UNCERTAINTY:
            assert issue.uncertainty is not None
            node_id = self.diagram.addChanceNode( # type: ignore
                gum.LabelizedVariable(
                    issue.id.__str__(),
                    issue.description,
                    sorted([outcome.id.__str__() for outcome in issue.uncertainty.outcomes]),
                )
            )
            self.add_to_lookup(issue, node_id)
        
        if issue.type == Type.UTILITY:
            assert issue.utility is not None
            node_id = self.diagram.addUtilityNode( # type: ignore
                gum.LabelizedVariable(
                    f"{issue.id.__str__()}",
                    f"{issue.id.__str__()}",
                    1,
                )
            )
            self.add_to_lookup(issue, node_id)

    def add_edge(self, edge: EdgeOutgoingDto):
        tail_id = self.node_lookup[edge.tail_node.issue_id.__str__()]
        head_id = self.node_lookup[edge.head_node.issue_id.__str__()]

        self.diagram.addArc(tail_id, head_id) # type: ignore

    def fill_cpts(self, issues: list[IssueOutgoingDto]):
        [self.fill_cpt(x) for x in issues]

    def fill_cpt(self, issue: IssueOutgoingDto):
        if issue.type != Type.UNCERTAINTY:
            return
        assert issue.uncertainty is not None

        node_id = self.node_lookup[issue.id.__str__()]
        parent_ids: list[int] = self.diagram.parents(node_id) # type: ignore
        parent_labels = [self.diagram.variable(pid).labels() for pid in parent_ids] # type: ignore

        # Build all parent state combinations
        parent_combinations = list(product(*parent_labels))

        discrete_probability_manager = DiscreteProbabilityArrayManager(issue.uncertainty.discrete_probabilities)

        cpt = self.diagram.cpt(node_id) # type: ignore
        if len(parent_ids) == 0:
            probabilities = discrete_probability_manager.get_probabilities_for_combination([])
            probabilities = self._probability_scaling(probabilities)
            cpt[:] = probabilities
            return cpt
        
        for parent_state in parent_combinations:
            probabilities = discrete_probability_manager.get_probabilities_for_combination(list(parent_state))
            probabilities = self._probability_scaling(probabilities)
            assign = {self.diagram.variable(parent_id).name(): outcome_id for parent_id, outcome_id in zip(parent_ids, parent_state)} # type: ignore
            cpt[assign] = probabilities
        return cpt
    
    def _probability_scaling(self, probabilities: list[float], scale: bool = False):
        # always default to no scaling for now
        if scale and len(probabilities) > 0:
            total = sum(probabilities)
            if total > 0:
                probabilities = [p / total for p in probabilities]
            else:
                probabilities = [1.0 / len(probabilities)] * len(probabilities)
            return probabilities
        else: 
            return probabilities

    def fill_utility_table(self, issue: IssueOutgoingDto):
        if issue.type in [Type.DECISION.value, Type.UNCERTAINTY.value]:
            return
        assert issue.utility is not None

        node_id = self.node_lookup[issue.id.__str__()]
        parent_ids: list[int] = self.diagram.parents(node_id) # type: ignore
        parent_labels = [self.diagram.variable(pid).labels() for pid in parent_ids] # type: ignore

        # Build all parent state combinations
        parent_combinations = list(product(*parent_labels))
        for combination in parent_combinations:
            for utility in issue.utility.discrete_utilities:
                parents = [str(option_id) for option_id in utility.parent_option_ids] + [str(outcome_id) for outcome_id in utility.parent_outcome_ids]
                if all([x in parents for x in combination]):
                    assign = {
                        self.diagram.variable(parent_id).name(): state # type: ignore
                        for parent_id, state in zip(parent_ids, combination)
                    } # type: ignore
                    self.diagram.utility(node_id)[assign] = utility.utility_value # type: ignore

    def add_virtual_utility_node(self, issue: IssueOutgoingDto):
        if issue.type == Type.UTILITY.value:
            return
        node_id = self.diagram.addUtilityNode( # type: ignore
            gum.LabelizedVariable(
                f"{issue.id.__str__()} utility",
                f"{issue.id.__str__()} utility",
                1,
            )
        )
        self.diagram.addArc(self.diagram.idFromName(issue.id.__str__()), node_id) # type: ignore

        if issue.type == Type.DECISION:
            assert issue.decision is not None

            for n, x in enumerate(self._sort_state_dtos(issue.decision.options)):
                self.diagram.utility(node_id)[{issue.id.__str__(): n}] = x.utility # type: ignore

        if issue.type == Type.UNCERTAINTY:
            assert issue.uncertainty is not None

            for n, x in enumerate(self._sort_state_dtos(issue.uncertainty.outcomes)):
                self.diagram.utility(node_id)[{issue.id.__str__(): n}] = x.utility # type: ignore

    def add_edges(self, edges: list[EdgeOutgoingDto]):
        [self.add_edge(x) for x in edges]

    def add_nodes(self, issues: list[IssueOutgoingDto]):
        [self.add_node(x) for x in issues]

    def add_virtual_utilities(self, issues: list[IssueOutgoingDto]):
        [self.add_virtual_utility_node(x) for x in issues]

    def fill_utilities(self, issues: list[IssueOutgoingDto]):
        [self.fill_utility_table(x) for x in issues]
