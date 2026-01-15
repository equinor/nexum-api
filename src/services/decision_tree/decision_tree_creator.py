from __future__ import annotations

import logging
import uuid
import copy
import itertools
import networkx as nx
from typing import Optional, Dict, Any, Union, List, Tuple, Iterator
from fastapi import HTTPException
from src.constants import Type
from src.seed_database import GenerateUuid
from src.dtos.issue_dtos import IssueOutgoingDto
from src.dtos.edge_dtos import EdgeOutgoingDto
from src.dtos.option_dtos import OptionOutgoingDto
from src.dtos.outcome_dtos import OutcomeOutgoingDto
from src.dtos.decision_tree_dtos import (
    EdgeUUIDDto,
    EndPointNodeDto,
    DecisionTreeDTO,
    TreeNodeDto,
    ProbabilityDto,
    UtilityDTDto
)
from src.dtos.discrete_probability_dtos import DiscreteProbabilityOutgoingDto

logger = logging.getLogger(__name__)


class DecisionTreeGraph:
    """Decision tree class"""

    def __init__(self, root: Optional[Any] = None, **kwargs: Dict[str, Any]) -> None:
        self.nx: nx.DiGraph = nx.DiGraph(**kwargs)  # type: ignore
        self.root: Optional[Any] = root
        if self.root is not None:
            self.nx.add_node(self.root)  # type: ignore
        self.treenode_lookup: Dict[str, TreeNodeDto] = {}
        self.outcomes_lookup: Dict[str, str] = {}
        self.edge_names: Dict[Tuple[uuid.UUID, uuid.UUID], str] = {}
        self.utility_lookup : Dict[tuple[str, ...], List[float]] = {}

    async def add_node(self, node: uuid.UUID) -> None:
        self.nx.add_node(node)  # type: ignore

    async def add_edge(self, edge: EdgeUUIDDto) -> None:
        self.nx.add_edge(edge.tail, edge.head, name=edge.name)  # type: ignore

    async def get_parent(self, node: uuid.UUID) -> Optional[uuid.UUID]:
        parents = list(self.nx.predecessors(node))  # type: ignore
        return parents[0] if (parents and len(parents) > 0) else None  # type: ignore

    async def populate_utility_lookup(self) -> None:
        for node in self.treenode_lookup.values():
            if isinstance(node.issue, EndPointNodeDto) or node.issue.type != Type.UTILITY.value:
                continue
            utility = node.issue.utility
            if utility and utility.discrete_utilities:
                for discrete_utility in utility.discrete_utilities:
                    if discrete_utility.utility_value:
                        parents = tuple(
                            sorted(p.__str__() for p in discrete_utility.parent_outcome_ids + discrete_utility.parent_option_ids)
                        )
                        self.utility_lookup.setdefault(parents, []).append(discrete_utility.utility_value)

    async def to_issue_dtos(self) -> Optional[DecisionTreeDTO]:
        await self.populate_utility_lookup()
        self.edge_names = nx.get_edge_attributes(self.nx, "name")  # type: ignore
        tg = nx.readwrite.json_graph.tree_data(self.nx, self.root)  # type: ignore
        tree_structure = await self.create_decision_tree_dto_from_treenode(tg)  # type: ignore
        return tree_structure

    async def get_decision_tree_dto(
        self, issue: TreeNodeDto, children: list[DecisionTreeDTO] | None = None
    ) -> DecisionTreeDTO:
        return DecisionTreeDTO(tree_node=issue, children=children)

    async def create_decision_tree_dto_from_treenode(
        self, tree_data: Dict[str, Any]
    ) -> Optional[DecisionTreeDTO]:
        # Base case: if the tree data is empty, return None
        if not tree_data:
            return None

        # Create the DTO for the current node
        node = self.treenode_lookup.get(str(tree_data["id"]), None)

        if node is None:
            return None

        # Recursively create DTOs for child nodes
        children_dtos: list[DecisionTreeDTO] = []
        for child in tree_data.get("children", []):
            child_dto = await self.create_decision_tree_dto_from_treenode(child)
            if child_dto:
                children_dtos.append(child_dto)

        copy_node = copy.deepcopy(node)
        copy_node.probabilities = await self.get_probability_values(copy_node)
        copy_node.utilities = await self.get_utility_values(copy_node)
        copy_node.id = await self.create_treenode_id(copy_node)
        return await self.get_decision_tree_dto(
            issue=copy_node, children=children_dtos if children_dtos else None
        )

    async def create_treenode_id(self, node: TreeNodeDto) -> uuid.UUID:
        id_string = ""
        treenode_id = node.id

        parent_id = await self.get_parent(treenode_id)
        count = 0
        while parent_id and count < 1000:
            n = self.edge_names[(parent_id, treenode_id)]
            id_string = n if id_string == "" else n + " - " + id_string
            treenode_id = parent_id
            parent_id = await self.get_parent(treenode_id)
            count += 1

        id_string = "root" if id_string == "" else "root" + " - " + id_string
        return GenerateUuid.as_uuid(id_string)

    async def find_matching_probabilities_dtos(
        self, object_uuids: list[uuid.UUID], in_dtos: list[DiscreteProbabilityOutgoingDto]
    ):
        out_dtos: list[DiscreteProbabilityOutgoingDto] = []
        for dto in in_dtos:
            combined_set = set(dto.parent_option_ids).union(set(dto.parent_outcome_ids))
            if set(combined_set).issubset(set(object_uuids)):
                out_dtos.append(dto)
        return out_dtos

    async def get_probability_values(self, node: TreeNodeDto) -> Optional[list[ProbabilityDto]]:
        treenode_id = node.id
        issue = node.issue
        probability_dtos: list[ProbabilityDto] = []

        if (
            isinstance(issue, IssueOutgoingDto)
            and issue.type == Type.UNCERTAINTY.value
            and issue.uncertainty is not None
            and len(issue.uncertainty.discrete_probabilities) > 0
        ):
            parent_labels: list[uuid.UUID] = []
            parent_id = await self.get_parent(treenode_id)
            count = 0
            while parent_id and count < 1000:
                parent_labels.append(uuid.UUID(self.edge_names[(parent_id, treenode_id)]))
                treenode_id = parent_id
                parent_id = await self.get_parent(treenode_id)
                count += 1

            discrete_prob_dtos = await self.find_matching_probabilities_dtos(
                parent_labels, issue.uncertainty.discrete_probabilities
            )

            for dto in discrete_prob_dtos:
                if dto.probability is not None:
                    probability_dto = ProbabilityDto(
                        outcome_name=self.outcomes_lookup[dto.outcome_id.__str__()],
                        outcome_id=dto.outcome_id,
                        probability_value=dto.probability,
                        discrete_probability_id=dto.id,
                    )
                    probability_dtos.append(probability_dto)

        return probability_dtos

    async def get_utility_values(self, node: TreeNodeDto) -> Optional[list[UtilityDTDto]]:
        issue = node.issue
        utility_dtos : list[UtilityDTDto] = []
        if (isinstance(issue, EndPointNodeDto)):
            return utility_dtos

        if issue.type == Type.UNCERTAINTY.value and issue.uncertainty is not None:
            outcomes = issue.uncertainty.outcomes
            for outcome in outcomes:
                discrete_utility_value = await self.get_discrete_utility_value(node, outcome)
                utility_dto = UtilityDTDto(outcome_name=outcome.name,
                                           outcome_id=outcome.id,
                                           utility_value=outcome.utility + discrete_utility_value)
                utility_dtos.append(utility_dto)

        if issue.type == Type.DECISION.value and issue.decision is not None:
            options = issue.decision.options
            for option in options:
                discrete_utility_value = await self.get_discrete_utility_value(node, option)
                utility_dto = UtilityDTDto(option_name=option.name,
                                           option_id=option.id,
                                           utility_value=option.utility + discrete_utility_value)
                utility_dtos.append(utility_dto)

        return utility_dtos

    async def get_discrete_utility_value(self, node: TreeNodeDto, dto : OptionOutgoingDto | OutcomeOutgoingDto) -> float:
        branch_label = dto.id.__str__()
        if not any(branch_label in key for key in self.utility_lookup.keys()):
            return 0

        node_id = node.id
        branch_labels = [branch_label]

        # Add branch labels for predecessors to the treenode branch
        parent_id = await self.get_parent(node_id)
        count = 0
        while parent_id and count < 1000:
            branch_labels.append(self.edge_names[(parent_id, node_id)])
            node_id = parent_id
            parent_id = await self.get_parent(node_id)
            count += 1

        # Create list of branch combinations, must include branch label for treenode
        branch_combinations : list[tuple[str, ...]] = [
            combo for r in range(2, len(branch_labels) + 1)
            for combo in itertools.combinations(branch_labels, r)
            if branch_label in combo]

        # Loop through branch_combinations
        # and add discrete utility for current treenode (from combinations present in utility_lookup)
        total_discrete_utility_value = sum(
                sum(self.utility_lookup[key])
                for combination in branch_combinations
                if (key := tuple(sorted(combination))) in self.utility_lookup
            ) if len(branch_labels) > 1 else 0

        return total_discrete_utility_value


class DecisionTreeCreator:
    def __init__(self) -> None:
        self.nx = nx.DiGraph()  # type: ignore
        self.project_id: uuid.UUID
        self.data: Dict[str, List[Union[uuid.UUID, EdgeUUIDDto]]] = {}
        self.treenode_ids: list[uuid.UUID] = []
        self.treenode_edge_dtos: list[EdgeUUIDDto] = []
        self.treenode_lookup: Dict[str, TreeNodeDto] = {}
        self.outcomes_lookup: Dict[str, str] = {}

    @classmethod
    async def initialize(
        cls, project_id: uuid.UUID, nodes: list[IssueOutgoingDto], edges: list[EdgeOutgoingDto]
    ) -> DecisionTreeCreator:
        instance = cls()
        instance.project_id = project_id
        treenodes = [TreeNodeDto(issue=node) for node in nodes]
        instance.treenode_ids, instance.treenode_edge_dtos = await instance.create_data_struct(
            treenodes, edges
        )
        instance.treenode_lookup = await instance.populate_treenode_lookup(treenodes)
        await instance.data_to_networkx(instance.treenode_ids, instance.treenode_edge_dtos)
        return instance

    async def populate_treenode_lookup(self, nodes: list[TreeNodeDto]) -> Dict[str, TreeNodeDto]:
        return {str(node.id): node for node in nodes}

    async def create_decision_tree(
        self, partial_order: Optional[list[uuid.UUID]] = None
    ) -> DecisionTreeGraph:
        return await self.convert_to_decision_tree(
            project_id=self.project_id, partial_order=partial_order
        )

    async def create_data_struct(
        self, nodes: list[TreeNodeDto], edges: list[EdgeOutgoingDto]
    ) -> Tuple[List[uuid.UUID], List[EdgeUUIDDto]]:
        node_ids = [node.id for node in nodes]
        edge_dtos = [await self.to_arc_dto(nodes, edge) for edge in edges]
        return node_ids, edge_dtos

    async def to_arc_dto(self, nodes: list[TreeNodeDto], edge: EdgeOutgoingDto) -> EdgeUUIDDto:
        tail_node = [x for x in nodes if x.issue.id == edge.tail_node.issue_id][0]
        head_node = [x for x in nodes if x.issue.id == edge.head_node.issue_id][0]
        return EdgeUUIDDto(tail=tail_node.id, head=head_node.id)

    async def data_to_networkx(
        self, node_ids: List[uuid.UUID], edge_dtos: List[EdgeUUIDDto]
    ) -> None:
        for node_id in node_ids:
            await self.add_node(node_id)
        for edge_dto in edge_dtos:
            await self.add_edge(edge_dto)

    async def add_node(self, node: uuid.UUID) -> None:
        try:
            self.nx.add_node(node)  # type: ignore
        except Exception as e:
            print("Exception Add_node", str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def add_edge(self, edge: EdgeUUIDDto) -> None:
        self.nx.add_edge(edge.tail, edge.head)  # type: ignore

    async def copy(self) -> DecisionTreeCreator:
        new_id = type(self)()  # Need to instance from the concrete class
        new_id.nx = self.nx.copy()  # type: ignore
        new_id.project_id = copy.deepcopy(self.project_id)
        new_id.treenode_lookup = copy.deepcopy(self.treenode_lookup)
        return new_id

    async def get_parents(self, node: uuid.UUID) -> list[uuid.UUID]:
        return list(self.nx.predecessors(node))  # type: ignore

    async def get_children(self, node: uuid.UUID) -> list[uuid.UUID]:
        return list(self.nx.successors(node))  # type: ignore

    async def get_node_from_uuid(self, uuid: uuid.UUID) -> Optional[TreeNodeDto]:
        return self.treenode_lookup.get(str(uuid), None)

    async def get_type_from_id(self, id: uuid.UUID) -> str:
        node = await self.get_node_from_uuid(id)
        return node.issue.type if node is not None else "Undefined"

    async def get_nodes_from_type(self, node_type_string: str) -> list[uuid.UUID]:
        node_list: list[uuid.UUID] = []
        for node in list(self.nx.nodes(data=True)):  # type: ignore
            node_id = node[0]  # type: ignore
            if await self.get_type_from_id(node_id) == node_type_string:  # type: ignore
                node_list.append(node_id)  # type: ignore
        return node_list

    async def has_children(self, node: uuid.UUID) -> bool:
        return len(await self.get_children(node)) > 0

    async def get_decision_nodes(self) -> list[uuid.UUID]:
        return await self.get_nodes_from_type(Type.DECISION.value)

    async def get_uncertainty_nodes(self) -> list[uuid.UUID]:
        return await self.get_nodes_from_type(Type.UNCERTAINTY.value)

    async def get_utility_nodes(self) -> list[uuid.UUID]:
        return await self.get_nodes_from_type(Type.UTILITY.value)

    @property
    async def decision_count(self) -> int:
        return len(await self.get_decision_nodes())

    @property
    async def uncertainty_count(self) -> int:
        return len(await self.get_uncertainty_nodes())

    @property
    async def utility_count(self) -> int:
        return len(await self.get_utility_nodes())

    async def decision_elimination_order(self) -> list[uuid.UUID]:
        cid_copy = await self.copy()

        decisions: list[uuid.UUID] = []
        decisions_count = await cid_copy.decision_count
        while decisions_count > 0:
            nodes: list[uuid.UUID] = list(cid_copy.nx.nodes())  # type: ignore
            for node in nodes:
                if not await cid_copy.has_children(node):
                    if await self.get_type_from_id(node) == Type.DECISION.value:
                        decisions.append(node)
                        decisions_count -= 1
                    cid_copy.nx.remove_node(node)  # type: ignore
        return decisions

    async def calculate_partial_order_issues(self) -> List[uuid.UUID]:
        partial_order = await self.calculate_partial_order()
        partial_order_issues = [self.treenode_lookup[id.__str__()].issue.id for id in partial_order]
        return partial_order_issues

    async def calculate_partial_order(self) -> list[uuid.UUID]:
        """Partial order algorithm
        TODO: handle utility nodes
        """

        # get all chance nodes
        uncertainty_nodes = await self.get_uncertainty_nodes()
        elimination_order = await self.decision_elimination_order()
        # TODO: Add utility nodes
        partial_order: list[uuid.UUID] = []

        while elimination_order:
            decision = elimination_order.pop()
            parent_decision_nodes: list[uuid.UUID] = []
            for parent in await self.get_parents(decision):
                if not await self.get_type_from_id(parent) == Type.DECISION.value:
                    if parent in uncertainty_nodes:
                        parent_decision_nodes.append(parent)
                        uncertainty_nodes.remove(parent)

            if len(parent_decision_nodes) > 0:
                partial_order += parent_decision_nodes
            partial_order.append(decision)

        partial_order += uncertainty_nodes

        return partial_order

    async def output_branches_from_node(
        self, node_id: uuid.UUID, node_in_partial_order_id: uuid.UUID, flip: bool = True
    ) -> Iterator[Tuple[EdgeUUIDDto, uuid.UUID]]:
        tree_stack = []
        node = await self.get_node_from_uuid(node_id)
        if node is not None and isinstance(node.issue, IssueOutgoingDto):
            if node.issue.type == Type.DECISION:
                tree_stack = (
                    [
                        EdgeUUIDDto(tail=node_id, head=None, name=option.id.__str__())
                        for option in node.issue.decision.options
                    ]
                    if node.issue.decision
                    else []
                )
            elif node.issue.type == Type.UNCERTAINTY:
                if node.issue.uncertainty is not None:
                    for outcome in node.issue.uncertainty.outcomes:
                        self.outcomes_lookup[outcome.id.__str__()] = outcome.name
                # This needs to be re-written according to the way we deal with probabilities
                tree_stack = (
                    [
                        EdgeUUIDDto(tail=node_id, head=None, name=outcome.id.__str__())
                        for outcome in node.issue.uncertainty.outcomes
                    ]
                    if node.issue.uncertainty
                    else []
                )
            if flip:
                tree_stack.reverse()

        return zip(tree_stack, [node_in_partial_order_id] * len(tree_stack), strict=False)

    async def convert_to_decision_tree(
        self, project_id: uuid.UUID, partial_order: Optional[list[uuid.UUID]] = None
    ) -> DecisionTreeGraph:
        # TODO: Update ID2DT according to way we deal with probabilities
        if not partial_order:
            partial_order = await self.calculate_partial_order()
        root_node = partial_order[0]
        decision_tree = DecisionTreeGraph(root=root_node)
        # tree_stack contains views of the partial order nodes
        # decision_tree contains copy of the nodes (as they appear several times)
        tree_stack = [(root_node, root_node)]

        while tree_stack:
            element = tree_stack.pop()

            if isinstance(element[0], uuid.UUID):  # type: ignore
                tree_stack += await self.output_branches_from_node(*element)  # type: ignore

            else:  # element is a branch
                endpoint_start_index = partial_order.index(element[1])

                if endpoint_start_index < len(partial_order) - 1:
                    endpoint_end = await self.copy_treenode(partial_order[endpoint_start_index + 1])
                    tree_stack.append((endpoint_end, partial_order[endpoint_start_index + 1]))
                else:
                    endpoint_end = await self.create_endpoint_node(project_id=project_id)

                element[0].head = endpoint_end
                await decision_tree.add_edge(element[0])  # node is added when the branch is added

        decision_tree.treenode_lookup = copy.deepcopy(self.treenode_lookup)
        decision_tree.outcomes_lookup = copy.deepcopy(self.outcomes_lookup)
        return decision_tree

    async def copy_treenode(self, node_id: uuid.UUID) -> uuid.UUID:
        # create a copy of the node, return id of the copy
        node = self.treenode_lookup[node_id.__str__()]
        copy_node = copy.deepcopy(node)
        copy_node.id = uuid.uuid4()
        self.treenode_lookup[copy_node.id.__str__()] = copy_node
        return copy_node.id

    async def create_endpoint_node(self, project_id: uuid.UUID) -> uuid.UUID:
        # create endpoint node which is added to treenode_lookup table, return id of the node
        node = EndPointNodeDto(project_id=project_id)
        treenode = TreeNodeDto(issue=node)
        self.treenode_lookup[treenode.id.__str__()] = treenode
        return treenode.id
