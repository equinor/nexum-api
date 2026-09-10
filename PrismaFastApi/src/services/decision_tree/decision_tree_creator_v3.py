from __future__ import annotations

import logging
import uuid
import numpy as np
import networkx as nx
from collections import defaultdict
from typing import Optional, Dict, Any, Union, List, Tuple, Iterator, Set, cast
from fastapi import HTTPException
from src.utils.generate_uuid import GenerateUuid
from src.constants import Type
from src.dtos.issue_dtos import IssueOutgoingDto
from src.dtos.edge_dtos import EdgeOutgoingDto
from src.dtos.discrete_probability_dtos import DiscreteProbabilityOutgoingDto
from src.dtos.discrete_utility_dtos import DiscreteUtilityOutgoingDto
from src.dtos.option_dtos import OptionOutgoingDto
from src.dtos.outcome_dtos import OutcomeOutgoingDto
from src.dtos.decision_tree_dtos import (
    EdgeUUIDDto,
    EndPointNodeDto,
    TreeNodeDto2,
    ProbabilityDto2,
    UtilityDTDto2,
)
from src.services.decision_tree.decision_tree_utils import NodeTreeNodeLookup

logger = logging.getLogger(__name__)


class MaxDepthExceededError(Exception):
    pass


class DecisionTreeGraph_v3:
    """Decision tree class"""

    ROOT = "root"
    DASH = "-"
    MAXDEPTH = 1000

    def __init__(self, root: uuid.UUID, **kwargs: Dict[str, Any]) -> None:
        self.nx: nx.DiGraph = nx.DiGraph(**kwargs)  # type: ignore
        self.root: uuid.UUID = root
        self.edge_names: Dict[Tuple[uuid.UUID, uuid.UUID], str] = {}
        self.utility_lookup: Dict[tuple[str, ...], List[float]] = {}
        self.discrete_probability_lookup = defaultdict(set)
        self.node_treenode_lookup: NodeTreeNodeLookup
        self.final_expected_value: float = 0
        self.treenode_oldid_to_newid_map: Dict[uuid.UUID, uuid.UUID] = {}
        self.treenodeid_to_parentid_map : Dict[uuid.UUID, Optional[uuid.UUID]] = {}
        self.treenodeid_to_parentid_map[self.root] = None
        self.discrete_probabilities: list[DiscreteProbabilityOutgoingDto] = []
        self.discrete_utilities: list[DiscreteUtilityOutgoingDto] = []

    def add_edge(self, edge: EdgeUUIDDto) -> None:
        self.treenodeid_to_parentid_map[edge.head] = edge.tail
        self.edge_names[(edge.tail, edge.head)] = edge.name

    def transfer_node_treenode_lookup(self, lookup: NodeTreeNodeLookup) -> None:
        self.node_treenode_lookup = lookup

    def get_parent(self, node_id: uuid.UUID) -> Optional[uuid.UUID]:
        return self.treenodeid_to_parentid_map.get(node_id)

    def populate_utility_lookup(self) -> None:
        for node_id in self.node_treenode_lookup.treenode_id_to_node_id.values():  # type: ignore
            node = self.node_treenode_lookup.get_node_dto(node_id)
            if node:
                if isinstance(node, EndPointNodeDto) or node.type != Type.UTILITY.value:
                    continue
                utility = node.utility
                if utility is not None:
                    for discrete_utility in self.discrete_utilities:
                        if discrete_utility.utility_id != utility.id:
                            continue
                        parents = tuple(
                            sorted(
                                p.__str__()
                                for p in discrete_utility.parent_outcome_ids
                                + discrete_utility.parent_option_ids
                            )
                        )
                        self.utility_lookup.setdefault(parents, []).append(
                            discrete_utility.utility_value
                        )

    def populate_discrete_probabilities_lookup(self) -> None:
        for node_id in self.node_treenode_lookup.treenode_id_to_node_id.values():  # type: ignore
            node = self.node_treenode_lookup.get_node_dto(node_id)
            if node:
                if isinstance(node, EndPointNodeDto) or node.type != Type.UNCERTAINTY.value:
                    continue
                uncertainty = node.uncertainty
                if uncertainty:
                    for discrete_probability in self.discrete_probabilities:
                        if discrete_probability.uncertainty_id != uncertainty.id:
                            continue
                        parents = tuple(
                            sorted(
                                str(p)
                                for p in discrete_probability.parent_outcome_ids
                                + discrete_probability.parent_option_ids
                            )
                        )
                        self.discrete_probability_lookup[parents].add(
                            (discrete_probability.outcome_id, discrete_probability.probability)
                        )

    def get_dto_map(self):
        dto_map: Dict[uuid.UUID, TreeNodeDto2] = {}
        for treenode_id in self.treenodeid_to_parentid_map.keys():
            if node := self.node_treenode_lookup.get_dto_for_treenode_id(treenode_id):
                type = Type.END.value if isinstance(node, EndPointNodeDto) else node.type
                parent_state_id: Optional[str] = self.edge_names.get((self.get_parent(treenode_id), treenode_id))
                dto = TreeNodeDto2(
                    parent_state_id=parent_state_id,
                    id=treenode_id,
                    issue_id = node.id,
                    type = type,
                    probabilities = self.get_discrete_probability_dtos(treenode_id, node),
                    utilities = self.get_utility_dtos(treenode_id, node),
                    children=[],
                )
                if dto.utilities:
                    dto.utilities.sort(key=lambda x: str(x.option_id if x.option_id is not None else x.outcome_id or ""))

                if dto.probabilities:
                    dto.probabilities.sort(key=lambda x: x.outcome_id)

                dto_map[treenode_id] = dto

        for parent_id in self.treenodeid_to_parentid_map.keys():
            parent_dto = dto_map.get(parent_id)
            if parent_dto is not None:
                # Get child node ids (outgoing edges from parent)
                child_ids: List[uuid.UUID] = list(self.get_successors(parent_id)) # type: ignore
                # Set children as list of DTOs
                parent_dto.children = [
                    dto_map[child_id] for child_id in child_ids if child_id in dto_map
                ]
                parent_dto.children.sort(key=lambda x: x.parent_state_id or "")

        return dto_map

    def get_successors(self, parent_id: uuid.UUID):
        return [k for k, v in self.treenodeid_to_parentid_map.items() if v == parent_id]

    def topological_sort(self, dto_map: Dict[uuid.UUID, TreeNodeDto2]) -> List[uuid.UUID]:
        visited: Set[uuid.UUID] = set()
        order: List[uuid.UUID] = []

        def visit(node_id: uuid.UUID):
            if node_id in visited:
                return
            visited.add(node_id)
            node = dto_map.get(node_id)
            if node:
                for child in getattr(node, "children", []) or []:
                    visit(child.id)
            order.append(node_id)

        for node_id in dto_map:
            visit(node_id)
        return order

    def to_issue_dtos(self, backwards_calc: bool = True) -> Optional[TreeNodeDto2]:
        """
        backwards_calc: 
            if true, calculate expected values and probabilities from the bottom up; 
            if false, skip calculations and just convert structure to dtos 
            (used for partial trees where endpoints may be missing)
        """
        self.populate_utility_lookup() # create lookup for discrete utilities
        if backwards_calc:
            self.populate_discrete_probabilities_lookup() # create lookup for discrete probabilities
        dto_map = self.get_dto_map()
        self.calculate_endpoint_nodes(self.root, dto_map)
        if backwards_calc:
            self.final_expected_value = self.compute_expected_values(self.root, dto_map)
        dto_map = self.calculate_treenode_ids_from_branches(dto_map)
        root_id = self.find_root_id(dto_map)
        return dto_map[root_id] if root_id else None
    
    def calculate_treenode_ids_from_branches(self, dto_map: Dict[uuid.UUID, TreeNodeDto2]) -> Dict[uuid.UUID, TreeNodeDto2]:
        new_map: Dict[uuid.UUID, TreeNodeDto2] = {}
        for old_key, dto in dto_map.items():
            # Partial trees may not include any end nodes, so the usual end-node walk
            # never populates the map; derive a deterministic id from the branch path.
            new_id = self.get_or_create_treenode_new_id(old_key)
            dto.id = new_id  # Update the dto's id
            new_map[new_id] = dto
        return new_map

    def get_or_create_treenode_new_id(self, treenode_id: uuid.UUID) -> uuid.UUID:
        """
        Create a stable treenode id even when no end nodes exist.

        Partial decision trees often stop before endpoints, so the end-node traversal
        that normally builds treenode_oldid_to_newid_map never runs. In that case we
        still need deterministic ids for consumers, so we derive them from ancestor
        branch labels.
        """
        existing_id = self.treenode_oldid_to_newid_map.get(treenode_id)
        if existing_id is not None:
            return existing_id

        labels: list[str] = []
        current_id = treenode_id
        parent_id = self.get_parent(current_id)
        count = 0
        while parent_id and count < self.MAXDEPTH:
            labels.append(self.edge_names[(parent_id, current_id)])
            current_id = parent_id
            parent_id = self.get_parent(current_id)
            count += 1

        if count >= self.MAXDEPTH:
            raise MaxDepthExceededError(
                f"Maximum depth of {self.MAXDEPTH} reached while traversing parents."
            )

        id_string = self.DASH.join(labels)
        id_string = self.ROOT if id_string == "" else self.ROOT + self.DASH + id_string
        new_id = GenerateUuid.as_uuid(id_string)
        self.treenode_oldid_to_newid_map[treenode_id] = new_id
        return new_id

    def find_root_id(self, dto_map: Dict[uuid.UUID, TreeNodeDto2]) -> Optional[uuid.UUID]:
        all_ids: Set[uuid.UUID] = set(dto_map.keys())
        child_ids: Set[uuid.UUID] = set(
            child.id for dto in dto_map.values() if dto.children for child in dto.children
        )
        root_ids = list(all_ids - child_ids)
        if not root_ids:
            raise ValueError("No root node found")
        return root_ids[0] if len(root_ids) > 0 else None

    def get_probabilities(self, id: uuid.UUID, parent_node: TreeNodeDto2) -> float:
        branch_id = self.edge_names[(parent_node.id, id)]
        prob = self.get_probability_for_branch(parent_node, branch_id) if parent_node else 0
        return prob

    def compute_expected_values(
        self, root_id: uuid.UUID, dto_map: Dict[uuid.UUID, TreeNodeDto2]
    ) -> float:
        order = self.topological_sort(dto_map)
        for node_id in order:
            try:
                node = dto_map[node_id]
                if node.type == Type.END.value:
                    node.expected_value = None  # node.endpoint_value
                elif node.type == Type.UNCERTAINTY.value:
                    child_ids = [child.id for child in node.children]
                    child_values = np.array(
                        [
                            (
                                child.endpoint_value
                                if child.type == Type.END.value
                                else child.expected_value
                            )
                            for child in node.children
                        ]
                    )
                    probabilities = np.array([self.get_probabilities(id, node) for id in child_ids])
                    node.expected_value = np.dot(probabilities, child_values)
                elif node.type == Type.DECISION.value:
                    child_values = np.array([child.expected_value for child in node.children])
                    node.expected_value = np.max(child_values)
            except Exception as e:
                print(f"Exception at node_id={node_id}: {e}")
                import traceback

                traceback.print_exc()
                break

        return dto_map[root_id].expected_value

    def calculate_endpoint_nodes(
        self, root_id: uuid.UUID, dto_map: Dict[uuid.UUID, TreeNodeDto2]
    ) -> None:
        stack = [dto_map[root_id]]
        while stack:
            node = stack.pop()
            if node.type == Type.END.value:
                node.endpoint_value, node.cumulative_probability = self.calculate_endpoint_value(
                    node.id, dto_map
                )
                self.create_treenode_ids_from_endnode(node.id)
            elif node.children:
                stack.extend(node.children)

    def calculate_endpoint_value(
        self, id: uuid.UUID, dto_map: Dict[uuid.UUID, TreeNodeDto2]
    ) -> Tuple[float, float]:
        if not id:
            return 0, 0

        parent_id = self.get_parent(id)
        if not parent_id:
            return 0, 0
        count = 0
        node_value = 0
        cumulative_probability = 1
        branch_id = self.edge_names[(parent_id, id)]
        while parent_id and count < self.MAXDEPTH:
            parent_node = dto_map[parent_id]
            node_value += self.get_utility_for_branch(parent_node, branch_id) if parent_node else 0

            if parent_node and parent_node.type == Type.UNCERTAINTY.value:
                cumulative_probability *= self.get_probability_for_branch(parent_node, branch_id)
            id = parent_id
            parent_id = self.get_parent(id)
            if parent_id:
                branch_id = self.edge_names[(parent_id, id)]
            count += 1

        if count >= self.MAXDEPTH:
            raise MaxDepthExceededError(
                f"Maximum depth of {self.MAXDEPTH} reached while traversing parents."
            )

        return node_value, cumulative_probability

    def get_utility_for_branch(self, node: TreeNodeDto2, branch_id: str) -> float:
        if node.utilities:
            for utility in node.utilities:
                if (utility.option_id is not None and utility.option_id.__str__() == branch_id) or (
                    utility.outcome_id is not None and utility.outcome_id.__str__() == branch_id
                ):
                    return utility.utility_value
        return 0

    def get_probability_for_branch(self, node: TreeNodeDto2, branch_id: str) -> float:
        if node.probabilities:
            for probability in node.probabilities:
                if probability.outcome_id.__str__() == branch_id:
                    return probability.probability_value
        return 0

    def create_treenode_ids_from_endnode(self, treenode_id: uuid.UUID) -> None:
        node_id = treenode_id
        id_to_branchname_map: Dict[uuid.UUID, str] = {}
        parent_id = self.get_parent(node_id)
        count = 0
        while parent_id and count < self.MAXDEPTH:
            n = self.edge_names[(parent_id, node_id)]
            id_to_branchname_map[node_id] = n
            node_id = parent_id
            parent_id = self.get_parent(node_id)
            count += 1

        if count >= self.MAXDEPTH:
            raise MaxDepthExceededError(
                f"Maximum depth of {self.MAXDEPTH} reached while traversing parents."
            )

        # assume parent_id is root
        if self.treenode_oldid_to_newid_map.get(node_id) is None:
            self.treenode_oldid_to_newid_map[node_id] = GenerateUuid.as_uuid(self.ROOT)

        while id_to_branchname_map:
            id_string = ""
            first_key = next(iter(id_to_branchname_map))
            if self.treenode_oldid_to_newid_map.get(first_key) is None:
                values = list(id_to_branchname_map.values())
                id_string = self.DASH.join(values)
                id_string = self.ROOT if id_string == "" else self.ROOT + self.DASH + id_string
                new_id = GenerateUuid.as_uuid(id_string)
                self.treenode_oldid_to_newid_map[first_key] = new_id
                id_to_branchname_map.pop(first_key)
            else:
                break

    def get_discrete_probability_dtos(
        self, treenode_id: uuid.UUID, node: IssueOutgoingDto | EndPointNodeDto
    ) -> Optional[list[ProbabilityDto2]]:

        probability_dtos: list[ProbabilityDto2] = []
        if isinstance(node, EndPointNodeDto):
            return probability_dtos

        if (
            node.type == Type.UNCERTAINTY.value
            and node.uncertainty is not None
        ):
            uncertainty_discrete_probs = [dp for dp in self.discrete_probabilities if dp.uncertainty_id == node.uncertainty.id]
            if len(uncertainty_discrete_probs) > 0:
                ancestors_ids = self.get_ancestors_ids(treenode_id)
                parent_ids_list: list[set[str]] = []
                for dto in uncertainty_discrete_probs:
                    parent_ids: set[uuid.UUID] = set(dto.parent_option_ids).union(
                        set(dto.parent_outcome_ids)
                    )
                    parent_ids_str: set[str] = {str(uuid) for uuid in parent_ids}
                    if (
                        set(parent_ids_str).issubset(set(ancestors_ids))
                        and parent_ids_str not in parent_ids_list
                    ):
                        parent_ids_list.append(parent_ids_str)

                for parents in parent_ids_list:
                    parent_ids_t = tuple(sorted(p for p in parents))
                    discrete_probs = self.discrete_probability_lookup[parent_ids_t]
                    for probs in discrete_probs:
                        probability_dto = ProbabilityDto2(
                            outcome_id=probs[0],
                            probability_value=probs[1],
                        )
                        probability_dtos.append(probability_dto)
        return probability_dtos

    def get_ancestors_ids(self, treenode_id: uuid.UUID) -> list[str]:
        ancestors_ids: list[str] = []
        parent_id = self.get_parent(treenode_id)
        count = 0
        while parent_id and count < self.MAXDEPTH:
            ancestors_ids.append(self.edge_names[(parent_id, treenode_id)])
            treenode_id = parent_id
            parent_id = self.get_parent(treenode_id)
            count += 1
        if count >= self.MAXDEPTH:
            raise MaxDepthExceededError(
                f"Maximum depth of {self.MAXDEPTH} reached while traversing parents."
            )
        return ancestors_ids

    def get_utility_dtos(
        self, treenode_id: uuid.UUID, node: IssueOutgoingDto | EndPointNodeDto
    ) -> Optional[list[UtilityDTDto2]]:

        utility_dtos: list[UtilityDTDto2] = []
        if isinstance(node, EndPointNodeDto):
            return utility_dtos

        if node.type == Type.UNCERTAINTY.value and node.uncertainty is not None:
            outcomes = node.uncertainty.outcomes
            for outcome in outcomes:
                discrete_utility_value = self.get_discrete_utility_value(treenode_id, outcome)
                utility_dto = UtilityDTDto2(
                    outcome_id=outcome.id, name=outcome.name, utility_value=outcome.utility + discrete_utility_value
                )
                utility_dtos.append(utility_dto)

        if node.type == Type.DECISION.value and node.decision is not None:
            options = node.decision.options
            for option in options:
                discrete_utility_value = self.get_discrete_utility_value(treenode_id, option)
                utility_dto = UtilityDTDto2(
                    option_id=option.id, name=option.name, utility_value=option.utility + discrete_utility_value
                )
                utility_dtos.append(utility_dto)

        return utility_dtos

    def get_discrete_utility_value(
        self, treenode_id: uuid.UUID, dto: OptionOutgoingDto | OutcomeOutgoingDto
    ) -> float:
        last_node_id = self.node_treenode_lookup.get_dto_id_for_treenode_id(treenode_id)
        if last_node_id not in self.node_treenode_lookup.treenode_id_to_utility_id:
            return 0
        branch_label = dto.id.__str__()

        branch_labels = [branch_label]
        # Add branch labels for predecessors to the treenode branch
        ancestors_ids = self.get_ancestors_ids(treenode_id)
        branch_labels.extend(ancestors_ids)

        branch_labels_list = tuple(branch_labels)
        matching_keys = [
            k for k in self.utility_lookup.keys() if set(k).issubset(branch_labels_list)
        ]
        return sum(
            sum(self.utility_lookup[key])
            for key in matching_keys
        )


class DecisionTreeCreator_v3:
    def __init__(self) -> None:
        self.nx = nx.DiGraph()  # type: ignore
        self.project_id: uuid.UUID
        self.data: Dict[str, List[Union[uuid.UUID, EdgeUUIDDto]]] = {}
        self.treenode_ids: list[uuid.UUID] = []
        self.node_ids: list[uuid.UUID] = []
        self.treenode_edge_dtos: list[EdgeUUIDDto] = []
        self.node_treenode_lookup: NodeTreeNodeLookup
        self.discrete_probabilities: list[DiscreteProbabilityOutgoingDto] = []
        self.discrete_utilities: list[DiscreteUtilityOutgoingDto] = []

    @classmethod
    def initialize(
        cls,
        project_id: uuid.UUID,
        nodes: list[IssueOutgoingDto],
        edges: list[EdgeOutgoingDto],
        discrete_probabilities: list[DiscreteProbabilityOutgoingDto] = [],
        discrete_utilities: list[DiscreteUtilityOutgoingDto] = [],
    ) -> DecisionTreeCreator_v3:
        instance = cls()
        instance.project_id = project_id
        instance.discrete_probabilities = discrete_probabilities
        instance.discrete_utilities = discrete_utilities
        instance.node_treenode_lookup = NodeTreeNodeLookup()
        # create a lookup between treenode id and IssueOutgoingDto | EndPointNodeDto
        instance.create_data_structure(nodes, edges)
        return instance

    def create_decision_tree(
        self, partial_order: Optional[list[uuid.UUID]] = None
    ) -> DecisionTreeGraph_v3:
        return self.convert_to_decision_tree(
            project_id=self.project_id, partial_order=partial_order
        )
    
    def create_decision_tree_partial(
        self, partial_order: Optional[list[uuid.UUID]] = None,
        paths: Optional[list[list[uuid.UUID]]] = None,
    ) -> DecisionTreeGraph_v3:
        if paths is None:
            paths = []
        return self.convert_to_decision_tree_partial(
            project_id=self.project_id, partial_order=partial_order, paths=paths
        )

    def create_data_structure(
        self, nodes: list[IssueOutgoingDto], edges: list[EdgeOutgoingDto]
    ) -> None:
        for node in nodes:
            treenode_id = uuid.uuid4()

            self.node_treenode_lookup.add_node_dto_and_treenode_id(node, treenode_id)
            self.add_node(treenode_id)

        for edge in edges:
            tail_node = [x for x in nodes if x.id == edge.tail_issue_id][0]
            head_node = [x for x in nodes if x.id == edge.head_issue_id][0]
            tail_treenode_id = self.node_treenode_lookup.get_treenode_ids_for_dto(tail_node.id)[0]
            head_treenode_id = self.node_treenode_lookup.get_treenode_ids_for_dto(head_node.id)[0]
            self.add_edge(EdgeUUIDDto(tail=tail_treenode_id, head=head_treenode_id))

    def add_node(self, node: uuid.UUID) -> None:
        try:
            self.nx.add_node(node)  # type: ignore
        except Exception as e:
            print("Exception Add_node", str(e))
            raise HTTPException(status_code=500, detail=str(e))

    def add_edge(self, edge: EdgeUUIDDto) -> None:
        self.nx.add_edge(edge.tail, edge.head)  # type: ignore

    def copy(self) -> DecisionTreeCreator_v3:
        new_id = type(self)()  # Need to instance from the concrete class
        new_id.nx = self.nx.copy()  # type: ignore
        new_id.project_id = self.project_id
        new_id.node_treenode_lookup = self.node_treenode_lookup
        return new_id

    def get_parents(self, node: uuid.UUID) -> list[uuid.UUID]:
        return list(self.nx.predecessors(node))  # type: ignore

    def get_children(self, node: uuid.UUID) -> list[uuid.UUID]:
        return list(self.nx.successors(node))  # type: ignore

    def get_node_from_uuid(self, uuid: uuid.UUID) -> Optional[IssueOutgoingDto | EndPointNodeDto]:
        return self.node_treenode_lookup.get_dto_for_treenode_id(uuid)

    def get_type_from_id(self, id: uuid.UUID) -> str:
        node = self.get_node_from_uuid(id)
        return node.type if node is not None else "Undefined"

    def get_nodes_from_type(self, node_type_string: str) -> list[uuid.UUID]:
        node_list: list[uuid.UUID] = []
        for node in list(self.nx.nodes(data=True)):  # type: ignore
            node_id = node[0]  # type: ignore
            if self.get_type_from_id(node_id) == node_type_string:  # type: ignore
                node_list.append(node_id)  # type: ignore
        return node_list

    def has_children(self, node: uuid.UUID) -> bool:
        return len(self.get_children(node)) > 0

    def get_decision_nodes(self) -> list[uuid.UUID]:
        return self.get_nodes_from_type(Type.DECISION.value)

    def get_uncertainty_nodes(self) -> list[uuid.UUID]:
        return self.get_nodes_from_type(Type.UNCERTAINTY.value)

    def get_utility_nodes(self) -> list[uuid.UUID]:
        return self.get_nodes_from_type(Type.UTILITY.value)

    @property
    def decision_count(self) -> int:
        return len(self.get_decision_nodes())

    @property
    def uncertainty_count(self) -> int:
        return len(self.get_uncertainty_nodes())

    @property
    def utility_count(self) -> int:
        return len(self.get_utility_nodes())

    def decision_elimination_order(self) -> list[uuid.UUID]:
        cid_copy = self.copy()

        decisions: list[uuid.UUID] = []
        decisions_count = cid_copy.decision_count
        while decisions_count > 0:
            nodes: list[uuid.UUID] = list(cid_copy.nx.nodes())  # type: ignore
            for node in nodes:
                if not cid_copy.has_children(node):
                    if self.get_type_from_id(node) == Type.DECISION.value:
                        decisions.append(node)
                        decisions_count -= 1
                    cid_copy.nx.remove_node(node)  # type: ignore
        return decisions

    def calculate_partial_order_issue_ids(self) -> List[Optional[uuid.UUID]]:
        partial_order = self.calculate_partial_order()
        partial_order_issues = [
            self.node_treenode_lookup.get_dto_id_for_treenode_id(id) for id in partial_order
        ]
        return partial_order_issues

    def calculate_partial_order(self) -> list[uuid.UUID]:
        """Partial order algorithm"""
        # get all chance nodes and sort according to child/parent relationship
        uncertainty_subgraph = self.nx.subgraph(self.get_uncertainty_nodes())  # type: ignore
        uncertainty_nodes = list(nx.topological_sort(uncertainty_subgraph))  # type: ignore

        elimination_order = self.decision_elimination_order()
        # TODO: Add utility nodes
        partial_order: list[uuid.UUID] = []

        while elimination_order:
            decision = elimination_order.pop()
            parent_decision_nodes: list[uuid.UUID] = []
            for parent in self.get_parents(decision):
                if not self.get_type_from_id(parent) == Type.DECISION.value:
                    if parent in uncertainty_nodes:
                        parent_decision_nodes.append(parent)
                        uncertainty_nodes.remove(parent)

            if len(parent_decision_nodes) > 0:
                partial_order += parent_decision_nodes
            partial_order.append(decision)

        partial_order += uncertainty_nodes  # type: ignore

        return partial_order

    def output_branches_from_node(
        self, node_id: uuid.UUID, node_in_partial_order_id: uuid.UUID, flip: bool = True
    ) -> Iterator[Tuple[EdgeUUIDDto, uuid.UUID]]:
        tree_stack = []
        node = self.get_node_from_uuid(node_id)
        if node is not None and isinstance(node, IssueOutgoingDto):
            if node.type == Type.DECISION:
                tree_stack = (
                    [
                        EdgeUUIDDto(tail=node_id, head=None, name=option.id.__str__())
                        for option in node.decision.options
                    ]
                    if node.decision
                    else []
                )
            elif node.type == Type.UNCERTAINTY:
                # This needs to be re-written according to the way we deal with probabilities
                tree_stack = (
                    [
                        EdgeUUIDDto(tail=node_id, head=None, name=outcome.id.__str__())
                        for outcome in node.uncertainty.outcomes
                    ]
                    if node.uncertainty
                    else []
                )
            if flip:
                tree_stack.reverse()

        return zip(tree_stack, [node_in_partial_order_id] * len(tree_stack), strict=False)

    def convert_to_decision_tree(
        self, project_id: uuid.UUID, partial_order: Optional[list[uuid.UUID]] = None
    ) -> DecisionTreeGraph_v3:
        # TODO: Update ID2DT according to way we deal with probabilities
        if not partial_order:
            partial_order = self.calculate_partial_order()
        root_node = partial_order[0]
        decision_tree = DecisionTreeGraph_v3(root=root_node)
        # tree_stack contains views of the partial order nodes
        # decision_tree contains copy of the nodes (as they appear several times)
        tree_stack = [(root_node, root_node)]

        while tree_stack:
            element = tree_stack.pop()

            if isinstance(element[0], uuid.UUID):  # type: ignore
                tree_stack += self.output_branches_from_node(*element)  # type: ignore

            else:  # element is a branch
                endpoint_start_index = partial_order.index(element[1])

                if endpoint_start_index < len(partial_order) - 1:
                    endpoint_end = self.copy_treenode(partial_order[endpoint_start_index + 1])
                    tree_stack.append((endpoint_end, partial_order[endpoint_start_index + 1]))
                else:
                    endpoint_end = self.create_endpoint_node(project_id=project_id)

                element[0].head = endpoint_end

                decision_tree.add_edge(element[0])  # node is added when the branch is added

        self.find_nodes_for_utilities(partial_order)
        decision_tree.transfer_node_treenode_lookup(self.node_treenode_lookup)
        decision_tree.discrete_probabilities = self.discrete_probabilities
        decision_tree.discrete_utilities = self.discrete_utilities
        return decision_tree
    
    def convert_to_decision_tree_partial(
            self, 
            project_id: uuid.UUID, 
            partial_order: Optional[list[uuid.UUID]] = None,
            paths: Optional[list[list[uuid.UUID]]] = None,
    ) -> DecisionTreeGraph_v3:
        """
        Make the decision tree structure for only the provided paths.
        Must expand the tree so that the given paths reprent the tail tree node, 
        meaning that the tree is expanded 1 depth greater than specified allowing for iterative interaction from an interface.
        If no paths are provided, the returned tree contains only the root node and no expanded branches.
        Arguments: 
            project_id: uuid.UUID
                The id of the decision project
            partial_order: Optional[list[uuid.UUID]]
                list of issue ids and represents the order of the issues, the first element being the root node
            paths: list[list[uuid.UUID]] = []
                list of state ids (outcome/option ids) each path must represent the full path. 
                Example:
                paths = [[option_A_id, outcome_A_id], [option_A_id, outcome_B_id]]
        """

        if not partial_order:
            partial_order = self.calculate_partial_order()
        root_node = partial_order[0]
        decision_tree = DecisionTreeGraph_v3(root=root_node)
        if not paths:
            paths = []
        
        prefix_to_treenode = {(): root_node}

        visited_states: set[tuple[tuple[uuid.UUID, ...], uuid.UUID]] = set()

        # auto-expand the paths that are almost at the endnodes
        almost_endnode_paths = [path for path in paths if len(path) == len(partial_order) - 1]
        for path in almost_endnode_paths:
            state_id = path[-1]
            issue = self.get_node_from_uuid(partial_order[len(path)])

            # get the last states of the tree from the issues
            if issue is not None and isinstance(issue, IssueOutgoingDto):
                next_states = []
                if issue.type == Type.DECISION.value and issue.decision is not None:
                    next_states = [option.id for option in issue.decision.options]
                elif issue.type == Type.UNCERTAINTY.value and issue.uncertainty is not None:
                    next_states = [outcome.id for outcome in issue.uncertainty.outcomes]
            else:
                continue
            for last_state in next_states:
                if last_state != state_id:
                    new_path = path + [last_state]
                    paths.append(new_path)

        for path in paths:
            for k, state_id in enumerate(path):
                issue = self.get_node_from_uuid(partial_order[k])
                # validate that paths are correct according to the partial order
                if issue is not None and isinstance(issue, IssueOutgoingDto):
                    valid_state = False
                    if issue.type == Type.DECISION.value and issue.decision is not None:
                        valid_state = any(
                            option.id == state_id for option in issue.decision.options
                        )
                    elif issue.type == Type.UNCERTAINTY.value and issue.uncertainty is not None:
                        valid_state = any(
                            outcome.id == state_id for outcome in issue.uncertainty.outcomes
                        )
                    if not valid_state:
                        raise ValueError(f"Invalid path: state_id {state_id} not found in issue {partial_order[k]}")
                else:
                    raise ValueError(f"Invalid path: issue {partial_order[k]} not found or not an IssueOutgoingDto")
                
                prefix = tuple(path[:k])
                visit_key = (prefix, state_id)
                if visit_key in visited_states:
                    continue
                else:
                    visited_states.add(visit_key)
                tail_id = prefix_to_treenode[prefix]

                if k + 1 < len(partial_order):
                    # create a unique treenode per branch
                    head_id = self.copy_treenode(partial_order[k + 1])
                else:
                    head_id = self.create_endpoint_node(project_id)

                prefix_to_treenode[tuple(path[:k + 1])] = head_id

                edge = EdgeUUIDDto(tail=tail_id, name=str(state_id), head=head_id)
                decision_tree.add_edge(edge)
        del visited_states
        
        self.find_nodes_for_utilities(partial_order)
        decision_tree.transfer_node_treenode_lookup(self.node_treenode_lookup)
        decision_tree.discrete_probabilities = self.discrete_probabilities
        decision_tree.discrete_utilities = self.discrete_utilities
        return decision_tree

    def copy_treenode(self, treenode_id: uuid.UUID) -> uuid.UUID:
        node_id = self.node_treenode_lookup.get_dto_id_for_treenode_id(treenode_id)
        copy_node_id = uuid.uuid4()
        if node_id:
            self.node_treenode_lookup.associate_uuid(node_id, copy_node_id)
        return copy_node_id

    def create_endpoint_node(self, project_id: uuid.UUID) -> uuid.UUID:
        # create endpoint node which is added to treenode_lookup table, return id of the node
        node = EndPointNodeDto(project_id=project_id)
        treenode_id = uuid.uuid4()
        self.node_treenode_lookup.add_node_dto_and_treenode_id(node, treenode_id)
        return treenode_id

    def find_nodes_for_utilities(self, partial_order: List[uuid.UUID]):
        for treenode_id in self.nx.nodes:
            node = self.node_treenode_lookup.get_dto_for_treenode_id(treenode_id)
            if node.type == Type.UTILITY.value:
                edges_with_same_head = [s for s, t in self.nx.in_edges(treenode_id)]

                indices = {
                    elem: partial_order.index(elem)
                    for elem in edges_with_same_head
                    if elem in partial_order
                }
                last_elem = max(indices, key=lambda k: indices[k])
                last_node_id = self.node_treenode_lookup.get_dto_id_for_treenode_id(last_elem)
                self.node_treenode_lookup.add_utility(last_node_id, treenode_id)
