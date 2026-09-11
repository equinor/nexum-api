import json
import uuid
import pyagrum as gum  # type: ignore
from pathlib import Path
from itertools import product
from src.config import config
from src.constants import Type
from src.utils.discrete_probability_array_manager import DiscreteProbabilityArrayManager
from src.dtos.issue_dtos import IssueOutgoingDto
from src.dtos.edge_dtos import EdgeOutgoingDto
from src.dtos.option_dtos import OptionOutgoingDto
from src.dtos.discrete_probability_dtos import DiscreteProbabilityOutgoingDto
from src.dtos.discrete_utility_dtos import DiscreteUtilityOutgoingDto
from src.dtos.outcome_dtos import OutcomeOutgoingDto
from src.dtos.model_solution_dtos import (
    ParentState,
    OptimalOption,
    DecisionSolution,
    SolutionDto,
)
from src.services.decision_tree.decision_tree_creator import DecisionTreeCreator
from src.dtos.policy_table_dtos import PolicyTableRowDto
from typing import Any, TypeVar, Optional

T = TypeVar("T", OptionOutgoingDto, OutcomeOutgoingDto)

# run for each optimal solution


class PyagrumSolver:
    def __init__(self):
        self.node_lookup: dict[str, int] = {}
        self.diagram = gum.InfluenceDiagram()
        self.issues: list[IssueOutgoingDto] = []
        self.edges: list[EdgeOutgoingDto] = []
        self.discrete_probabilities: list[DiscreteProbabilityOutgoingDto] = []
        self.discrete_utilities: list[DiscreteUtilityOutgoingDto] = []
        self.ie: Optional[gum.ShaferShenoyLIMIDInference] = None
        self.partial_order: Optional[list[uuid.UUID]] = None

    def _reset_diagram(self):
        self.diagram = gum.InfluenceDiagram()

    def add_to_lookup(self, issue: IssueOutgoingDto, node_id: int) -> None:
        self.node_lookup[issue.id.__str__()] = node_id

    def build_influence_diagram(
        self,
        issues: list[IssueOutgoingDto],
        edges: list[EdgeOutgoingDto],
        discrete_probabilities: list[DiscreteProbabilityOutgoingDto],
        discrete_utilities: list[DiscreteUtilityOutgoingDto],
    ):
        self.issues = issues
        self.edges = edges
        self.discrete_probabilities = discrete_probabilities
        self.discrete_utilities = discrete_utilities
        self.add_nodes(issues)
        self.add_edges(edges)
        self.fill_cpts(issues)
        self.add_virtual_utilities(issues)
        self.fill_utilities(issues)

    def raise_if_issues_edges_not_set(self):
        if not self.issues:
            raise RuntimeError("Issues have not been set. Call build_influence_diagram first.")

    def _sort_state_dtos(self, dtos: list[T]) -> list[T]:
        return sorted(dtos, key=lambda x: x.id.__str__())

    def _find_state(
        self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None
    ) -> OptionOutgoingDto | OutcomeOutgoingDto:
        """Returns the option/outcome that matches the state id. Looks through the issues variable if included, otherwise looks through all issues in the model."""
        states: list[OptionOutgoingDto | OutcomeOutgoingDto] = []
        if issues:
            [
                states.extend(issue.decision.options)
                for issue in issues
                if issue.decision is not None
            ]
            [
                states.extend(issue.uncertainty.outcomes)
                for issue in issues
                if issue.uncertainty is not None
            ]
        else:
            [
                states.extend(issue.decision.options)
                for issue in self.issues
                if issue.decision is not None
            ]
            [
                states.extend(issue.uncertainty.outcomes)
                for issue in self.issues
                if issue.uncertainty is not None
            ]

        return [state for state in states if str(state.id) == state_id][0]

    def _find_state_decision(
        self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None
    ) -> OptionOutgoingDto:
        """Returns the option that matches the state id. Looks through the issues variable if included, otherwise looks through all issues in the model."""
        states: list[OptionOutgoingDto] = []
        if issues:
            [
                states.extend(issue.decision.options)
                for issue in issues
                if issue.decision is not None
            ]
        else:
            [
                states.extend(issue.decision.options)
                for issue in self.issues
                if issue.decision is not None
            ]

        return [state for state in states if str(state.id) == state_id][0]

    def _get_option_id_from_state(
        self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None
    ) -> uuid.UUID:
        """Return the option UUID represented by a decision-node state label."""
        state = self._find_state_decision(state_id, issues)
        return state.id

    def _find_state_uncertainty(
        self, state_id: str, issues: Optional[list[IssueOutgoingDto]] = None
    ) -> OutcomeOutgoingDto:
        """Returns the outcome that matches the state id. Looks through the issues variable if included, otherwise looks through all issues in the model."""
        states: list[OutcomeOutgoingDto] = []
        if issues:
            [
                states.extend(issue.uncertainty.outcomes)
                for issue in issues
                if issue.uncertainty is not None
            ]
        else:
            [
                states.extend(issue.uncertainty.outcomes)
                for issue in self.issues
                if issue.uncertainty is not None
            ]

        return [state for state in states if str(state.id) == state_id][0]

    def _pyagrum_optimal_decision_argmax(
        self, ie: gum.ShaferShenoyLIMIDInference, decision_issue_id: str
    ) -> list[dict[str, int]]:
        return ie.optimalDecision(decision_issue_id).argmax()[0]  # type: ignore

    def _pyagrum_get_mean_utility(
        self, ie: gum.ShaferShenoyLIMIDInference, node_name: str
    ) -> float:
        return ie.meanVar(node_name)["mean"]  # type: ignore

    def _pyagrum_get_node_labels(self, node_identifier: str | int) -> tuple[str]:
        return self.diagram.variable(node_identifier).labels()  # type: ignore

    def get_optimal_decisions(self, ie: gum.ShaferShenoyLIMIDInference, decision_issue_id: str):
        pyagrum_result: list[dict[str, int]] = self._pyagrum_optimal_decision_argmax(
            ie, decision_issue_id
        )
        optimal_decisions: list[OptimalOption] = []
        for result in pyagrum_result:
            optimal_state: OptionOutgoingDto = self._find_state_decision(
                self._pyagrum_get_node_labels(decision_issue_id)[result[decision_issue_id]]
            )
            parent_states: list[ParentState] = []

            for i, key in enumerate(result):
                # skip the decision in question
                if i == 0:
                    continue
                parent_state_id: str = self._pyagrum_get_node_labels(key)[result[key]]
                parent_state = self._find_state(parent_state_id)
                parent_states.append(ParentState(parent_id=uuid.UUID(key), state=parent_state))

            optimal_decisions.append(
                OptimalOption(
                    parent_states=parent_states,
                    decision_id=uuid.UUID(decision_issue_id),
                    state=optimal_state,
                )
            )

        return DecisionSolution(
            optimal_decisions=optimal_decisions,
            mean=self._pyagrum_get_mean_utility(ie, decision_issue_id),
        )

    def get_solution(self, ie: gum.ShaferShenoyLIMIDInference, decisions: list[str]) -> SolutionDto:
        return SolutionDto(
            decision_solutions=[self.get_optimal_decisions(ie, x) for x in decisions]
        )

    def get_inference(self) -> gum.ShaferShenoyLIMIDInference:
        if self.ie is None:
            raise RuntimeError(
                "Inference engine has not been initialized. Call build_inference_engine or find_optimal_decisions first."
            )
        return self.ie

    async def get_partial_order(self) -> list[uuid.UUID]:
        if self.partial_order is None:
            self.raise_if_issues_edges_not_set()
            decision_tree_creator = await DecisionTreeCreator.initialize(
                project_id=self.issues[0].project_id, nodes=self.issues, edges=self.edges
            )

            self.partial_order = await decision_tree_creator.calculate_partial_order_issues()
        return self.partial_order

    async def add_no_forgetting_assumption_using_partial_order(
        self, ie: gum.ShaferShenoyLIMIDInference
    ) -> None:
        partial_order = await self.get_partial_order()
        decision_ids = {issue.id for issue in self.issues if issue.type == Type.DECISION.value}
        partial_order_decisions = [x for x in partial_order if x in decision_ids]
        ie.addNoForgettingAssumption([str(x) for x in partial_order_decisions])  # type: ignore

    async def build_inference_engine(
        self,
        issues: list[IssueOutgoingDto],
        edges: list[EdgeOutgoingDto],
        discrete_probabilities: list[DiscreteProbabilityOutgoingDto],
        discrete_utilities: list[DiscreteUtilityOutgoingDto],
    ) -> gum.ShaferShenoyLIMIDInference:
        self.build_influence_diagram(issues, edges, discrete_probabilities, discrete_utilities)

        self.ie = gum.ShaferShenoyLIMIDInference(self.diagram)

        if not self.ie.isSolvable():
            # try adding no forgetting assumption for decision nodes in the partial order
            await self.add_no_forgetting_assumption_using_partial_order(self.ie)

        if not self.ie.isSolvable():
            raise RuntimeError("Influence diagram is not solvable")
        self.ie.makeInference()

        return self.ie

    async def find_optimal_decisions(
        self,
        issues: list[IssueOutgoingDto],
        edges: list[EdgeOutgoingDto],
        discrete_probabilities: list[DiscreteProbabilityOutgoingDto],
        discrete_utilities: list[DiscreteUtilityOutgoingDto],
    ) -> SolutionDto:
        await self.build_inference_engine(issues, edges, discrete_probabilities, discrete_utilities)
        partial_order = await self.get_partial_order()
        solution = self.get_solution(
            self.get_inference(),
            [
                str(x)
                for x in partial_order
                if x in [issue.id for issue in issues if issue.type == Type.DECISION.value]
            ],
        )
        return solution

    async def get_solutions_given_evidence(
        self,
        issues: list[IssueOutgoingDto],
        edges: list[EdgeOutgoingDto],
        evidence: list[list[uuid.UUID]],
        discrete_probabilities: list[DiscreteProbabilityOutgoingDto],
        discrete_utilities: list[DiscreteUtilityOutgoingDto],
    ) -> list[SolutionDto]:
        ie = await self.build_inference_engine(
            issues, edges, discrete_probabilities, discrete_utilities
        )
        solutions: list[SolutionDto] = []
        partial_order = await self.get_partial_order()
        for evidence_item in evidence:
            ie_with_evidence = self.set_evidence(ie, [str(x) for x in evidence_item])
            solution = self.get_solution(
                ie_with_evidence,
                [
                    str(x)
                    for x in partial_order
                    if x in [issue.id for issue in issues if issue.type == Type.DECISION.value]
                ],
            )
            solutions.append(solution)
        return solutions

    async def get_mean_expected_utilities_given_evidence(
        self,
        issues: list[IssueOutgoingDto],
        edges: list[EdgeOutgoingDto],
        discrete_probabilities: list[DiscreteProbabilityOutgoingDto],
        discrete_utilities: list[DiscreteUtilityOutgoingDto],
        evidence: list[list[uuid.UUID]],
    ) -> list[Optional[float]]:
        ie = await self.build_inference_engine(
            issues, edges, discrete_probabilities, discrete_utilities
        )
        MEUs: list[Optional[float]] = []
        for evidence_item in evidence:
            ie_with_evidence = self.set_evidence(ie, [str(x) for x in evidence_item])
            MEU: dict[str, float] = ie_with_evidence.MEU()
            MEUs.append(MEU.get("mean", None))  # type: ignore
        return MEUs

    # method for adding evidence to the inference engine, takes a list of state_id, method internally finds the corresponding issue and state, then adds the evidence to the inference engine
    def set_evidence(self, ie: gum.ShaferShenoyLIMIDInference, state_ids: list[str]):
        ie.eraseAllEvidence()  # type: ignore
        evidence: dict[int, str] = {}
        for state_id in state_ids:
            state = self._find_state(state_id)
            if isinstance(state, OptionOutgoingDto):
                issue = [
                    issue
                    for issue in self.issues
                    if issue.decision is not None
                    and any(option.id == state.id for option in issue.decision.options)
                ][0]
                node_id = self.node_lookup[issue.id.__str__()]
                evidence[node_id] = str(state.id)
            elif isinstance(state, OutcomeOutgoingDto):  # type: ignore
                issue = [
                    issue
                    for issue in self.issues
                    if issue.uncertainty is not None
                    and any(outcome.id == state.id for outcome in issue.uncertainty.outcomes)
                ][0]
                node_id = self.node_lookup[issue.id.__str__()]
                evidence[node_id] = str(state.id)
        ie.setEvidence(evidence)  # type: ignore
        ie.makeInference()
        return ie

    def get_expected_utility_given_path(self, issue_id: str, state_ids: list[str]) -> float:
        ie = self.get_inference()
        ie_with_evidence = self.set_evidence(ie, state_ids)
        expected_utility = self._pyagrum_get_mean_utility(ie_with_evidence, issue_id)
        return expected_utility

    def get_posterior_given_path(self, issue_id: str, state_ids: list[str]) -> dict[str, float]:
        ie = self.get_inference()
        ie_with_evidence = self.set_evidence(ie, state_ids)

        # For chance/uncertainty nodes, posterior returns probabilities in order of node labels
        # issue_id is the node name
        posterior = ie_with_evidence.posterior(issue_id)  # type: ignore
        labels = self._pyagrum_get_node_labels(issue_id)
        probs: list[float] = posterior.toarray().tolist()  # type: ignore
        state_to_probability = {label: prob for label, prob in zip(labels, probs)}  # type: ignore
        return state_to_probability

    def add_node(self, issue: IssueOutgoingDto):
        if issue.type == Type.DECISION:
            assert issue.decision is not None
            node_id = self.diagram.addDecisionNode(  # type: ignore
                gum.LabelizedVariable(
                    issue.id.__str__(),
                    issue.description,
                    sorted([option.id.__str__() for option in issue.decision.options]),
                )
            )
            self.add_to_lookup(issue, node_id)

        if issue.type == Type.UNCERTAINTY:
            assert issue.uncertainty is not None
            node_id = self.diagram.addChanceNode(  # type: ignore
                gum.LabelizedVariable(
                    issue.id.__str__(),
                    issue.description,
                    sorted([outcome.id.__str__() for outcome in issue.uncertainty.outcomes]),
                )
            )
            self.add_to_lookup(issue, node_id)

        if issue.type == Type.UTILITY:
            assert issue.utility is not None
            node_id = self.diagram.addUtilityNode(  # type: ignore
                gum.LabelizedVariable(
                    f"{issue.id.__str__()}",
                    f"{issue.id.__str__()}",
                    1,
                )
            )
            self.add_to_lookup(issue, node_id)

    def add_edge(self, edge: EdgeOutgoingDto):
        tail_id = self.node_lookup[edge.tail_issue_id.__str__()]
        head_id = self.node_lookup[edge.head_issue_id.__str__()]

        self.diagram.addArc(tail_id, head_id)  # type: ignore

    def fill_cpts(self, issues: list[IssueOutgoingDto]):
        [self.fill_cpt(x) for x in issues]

    def fill_cpt(self, issue: IssueOutgoingDto):
        if issue.type != Type.UNCERTAINTY:
            return
        assert issue.uncertainty is not None

        node_id = self.node_lookup[issue.id.__str__()]
        parent_ids: list[int] = self.diagram.parents(node_id)  # type: ignore
        parent_labels = [self.diagram.variable(pid).labels() for pid in parent_ids]  # type: ignore

        # Build all parent state combinations
        parent_combinations = list(product(*parent_labels))

        discrete_probability_manager = DiscreteProbabilityArrayManager(
            [dp for dp in self.discrete_probabilities if dp.uncertainty_id == issue.uncertainty.id],
        )

        cpt = self.diagram.cpt(node_id)  # type: ignore
        if len(parent_ids) == 0:
            probabilities = discrete_probability_manager.get_probabilities_for_combination([])
            probabilities = self._probability_scaling(probabilities)
            cpt[:] = probabilities
            return cpt

        for parent_state in parent_combinations:
            probabilities = discrete_probability_manager.get_probabilities_for_combination(
                list(parent_state)
            )
            probabilities = self._probability_scaling(probabilities)
            assign = {self.diagram.variable(parent_id).name(): outcome_id for parent_id, outcome_id in zip(parent_ids, parent_state)}  # type: ignore
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
        parent_ids: list[int] = self.diagram.parents(node_id)  # type: ignore
        parent_labels = [self.diagram.variable(pid).labels() for pid in parent_ids]  # type: ignore

        # Build all parent state combinations
        parent_combinations = list(product(*parent_labels))
        disc_utilities = [
            utility for utility in self.discrete_utilities if utility.utility_id == issue.utility.id
        ]
        for combination in parent_combinations:
            for utility in disc_utilities:
                parents = [str(option_id) for option_id in utility.parent_option_ids] + [
                    str(outcome_id) for outcome_id in utility.parent_outcome_ids
                ]
                if all([x in parents for x in combination]):
                    assign = {
                        self.diagram.variable(parent_id).name(): state  # type: ignore
                        for parent_id, state in zip(parent_ids, combination)
                    }  # type: ignore
                    self.diagram.utility(node_id)[assign] = utility.utility_value  # type: ignore

    def add_virtual_utility_node(self, issue: IssueOutgoingDto):
        if issue.type == Type.UTILITY.value:
            return

        if issue.type == Type.DECISION and issue.decision is not None:
            if all([option.utility == 0 for option in issue.decision.options]):
                return

        if issue.type == Type.UNCERTAINTY and issue.uncertainty is not None:
            if all([outcome.utility == 0 for outcome in issue.uncertainty.outcomes]):
                return

        node_id = self.diagram.addUtilityNode(  # type: ignore
            gum.LabelizedVariable(
                f"{issue.id.__str__()} utility",
                f"{issue.id.__str__()} utility",
                1,
            )
        )
        self.diagram.addArc(self.diagram.idFromName(issue.id.__str__()), node_id)  # type: ignore

        if issue.type == Type.DECISION and issue.decision is not None:
            for n, x in enumerate(self._sort_state_dtos(issue.decision.options)):
                self.diagram.utility(node_id)[{issue.id.__str__(): n}] = x.utility  # type: ignore

        if issue.type == Type.UNCERTAINTY and issue.uncertainty is not None:
            for n, x in enumerate(self._sort_state_dtos(issue.uncertainty.outcomes)):
                self.diagram.utility(node_id)[{issue.id.__str__(): n}] = x.utility  # type: ignore

    def add_edges(self, edges: list[EdgeOutgoingDto]):
        [self.add_edge(x) for x in edges]

    def add_nodes(self, issues: list[IssueOutgoingDto]):
        [self.add_node(x) for x in issues]

    def add_virtual_utilities(self, issues: list[IssueOutgoingDto]):
        [self.add_virtual_utility_node(x) for x in issues]

    def fill_utilities(self, issues: list[IssueOutgoingDto]):
        [self.fill_utility_table(x) for x in issues]

    def get_policy_table(self, decision_issue_id: str) -> list[PolicyTableRowDto]:
        ie = self.get_inference()
        optimal_decision_tensor = ie.optimalDecision(decision_issue_id)  # type: ignore
        return self._parse_policy_tensor(decision_issue_id, optimal_decision_tensor)

    def _get_option_id_from_policy_table_states(self, states: list[str]) -> str:
        option_ids = [
            str(option.id)
            for issue in self.issues
            if issue.decision is not None
            for option in issue.decision.options
        ]
        for state in states:
            if state in option_ids:
                return str(self._find_state_decision(state).id)

        raise ValueError("No option ID found in policy states")

    def _parse_policy_tensor(
        self, decision_issue_id: str, optimal_decision_tensor: Any
    ) -> list[PolicyTableRowDto]:
        """Flatten a policy tensor into row DTOs with ordered state labels and value.

        Iterates every Instantiation of the tensor, collects each variable's current
        label into `states` (in tensor variable order), and reads the cell value for
        that assignment.
        """
        inst: Any = gum.Instantiation(optimal_decision_tensor)
        variables: list[Any] = list(inst.variablesSequence())
        parsed_rows: list[PolicyTableRowDto] = []

        inst.setFirst()
        while not inst.end():
            states = [str(variable.label(inst.val(variable))) for variable in variables]
            value = float(optimal_decision_tensor.get(inst))
            parsed_rows.append(
                PolicyTableRowDto(
                    decision_id=uuid.UUID(decision_issue_id),
                    parent_state_ids=[uuid.UUID(state) for state in states],
                    option_id=uuid.UUID(self._get_option_id_from_policy_table_states(states)),
                    value=value,
                )
            )
            inst.inc()
        return parsed_rows

    def export_pyagrum_model(self) -> dict:
        directory = "src/pyagrum_data"
        file_name = f"{directory}/network.jgum"
        file_name_json = f"{directory}/network.json"
        Path(directory).mkdir(parents=True, exist_ok=True)
        gum.saveID(self.diagram, file_name)

        issue_names = {str(issue.id): issue.name for issue in self.issues}
        option_names = {
            str(option.id): option.name
            for issue in self.issues
            if issue.decision is not None
            for option in issue.decision.options
        }
        outcome_names = {
            str(outcome.id): outcome.name
            for issue in self.issues
            if issue.uncertainty is not None
            for outcome in issue.uncertainty.outcomes
        }
        id_to_name = issue_names | option_names | outcome_names

        with open(file_name, encoding="utf-8") as jgum_file:
            jgum = json.load(jgum_file)
        
        readable_model: dict = self._replace_ids(jgum, id_to_name)
        if config.SAVE_INFLUENCE_DIAGRAM:
            with open(file_name_json, "w", encoding="utf-8") as jgum_file:
                json.dump(readable_model, jgum_file, ensure_ascii=False, separators=(",", ":"))

        # return the json data as a dictionary
        return readable_model

    def _replace_ids(self, value: object, id_to_name: dict[str, str]) -> object:
        if isinstance(value, dict):
            return {
                self._replace_ids(key, id_to_name): self._replace_ids(nested_value, id_to_name)
                for key, nested_value in value.items()
            }
        if isinstance(value, list):
            return [self._replace_ids(item, id_to_name) for item in value]
        if isinstance(value, str):
            for entity_id, name in id_to_name.items():
                value = value.replace(entity_id, name)
        return value

    