import uuid
from src.constants import Type
from src.domain.graph import Graph
from src.dtos.issue_dtos import IssueOutgoingDto
from src.dtos.edge_dtos import EdgeOutgoingDto
from src.utils.set_joins import join_sets_with_common_elements
import json


class InfluenceDiagramDOT:
    """
    DOT applications light-weight Influence diagram format
    """

    # since this class can reconstruct itself this counter is checked
    # and iterated on every init to prevent infinite loops
    init_counter: int = 0
    max_reconstructions = 5
    tail_to_head_lookup: dict[uuid.UUID, uuid.UUID]
    head_to_tail_lookup: dict[uuid.UUID, uuid.UUID]
    start_nodes: set[uuid.UUID]
    end_nodes: set[uuid.UUID]
    graph: Graph

    def __init__(self, edges: list[EdgeOutgoingDto], issues: list[IssueOutgoingDto]) -> None:
        self.constructor(edges, issues)

    def constructor(self, edges: list[EdgeOutgoingDto], issues: list[IssueOutgoingDto]):
        if self.init_counter > self.max_reconstructions:
            raise RecursionError(
                f"Cyclical reconstruction of InfluenceDiagramDOT object detected. "
                f"Init counter is {self.init_counter}. This prevents infinite recursion "
                f"during object reconstruction in validate_diagram method."
            )

        self.init_counter += 1

        self.edges = edges
        self.issues = issues
        self.tail_to_head_lookup = {}
        self.head_to_tail_lookup = {}
        self._construct_lookups()
        self._find_start_and_end_nodes()
        self._build_graph()
        self.validate_diagram()

    def _construct_lookup(self, edge: EdgeOutgoingDto):
        self.tail_to_head_lookup[edge.tail_issue_id] = edge.head_issue_id
        self.head_to_tail_lookup[edge.head_issue_id] = edge.tail_issue_id

    def _construct_lookups(self):
        list(map(self._construct_lookup, self.edges))

    def _find_start_and_end_nodes(self):
        all_tail_ids = set(self.tail_to_head_lookup.keys())
        all_head_ids = set(self.head_to_tail_lookup.keys())
        self.start_nodes = all_tail_ids - all_head_ids  # Nodes with no incoming edges
        self.end_nodes = all_head_ids - all_tail_ids  # Nodes with no outgoing edges

    def _build_graph(self):
        self.graph = Graph()
        for edge in self.edges:
            self.graph.addEdge(edge.tail_issue_id, edge.head_issue_id)

    def _reconstruct_for_longest_node_path(self):
        seperated_graphs = self.find_seperated_graphs()

        if len(seperated_graphs) > 1:

            # find the path with the most amount of nodes (longest path)
            longest_path_nodes = max(seperated_graphs, key=len)

            if len(longest_path_nodes) == 0:
                raise ValueError("Longest path contains no nodes. ")

            # filter issues to only include those in the longest path
            filtered_issues = [issue for issue in self.issues if issue.id in longest_path_nodes]

            # filter edges to only include those where both tail and head are in the longest path
            filtered_edges = [
                edge
                for edge in self.edges
                if edge.tail_issue_id in longest_path_nodes
                and edge.head_issue_id in longest_path_nodes
            ]

            # reconstruct the instance with filtered data
            self.constructor(filtered_edges, filtered_issues)
            self.validate_diagram()
            self.init_counter = 0

    def validate_diagram(self):
        validation_errors = {}
        edge_validation_messages = ""

        if len(self.start_nodes) == 0 and len(self.end_nodes) == 0:
            edge_validation_messages += "Invalid influence diagram: no start nodes (nodes with no incoming edges) and no end nodes (nodes with no outgoing edges) found "

        elif len(self.start_nodes) == 0:
            edge_validation_messages += (
                "Invalid influence diagram: no start nodes (nodes with no incoming edges) found."
            )

        elif len(self.end_nodes) == 0:
            edge_validation_messages += (
                "Invalid influence diagram: no end nodes (nodes with no outgoing edges) found."
            )

        # Check for edges
        if len(self.edges) == 0:
            edge_validation_messages += "Invalid influence diagram: no edges found."

        if edge_validation_messages != "":
            validation_errors["Edges"] = edge_validation_messages.strip()
        # Check for issues
        if len(self.issues) == 0:
            validation_errors["NoIssues"] = "Invalid influence diagram: no issues found."

        # Check for cyclical paths
        is_cyclical = self.graph.detectCycle()
        if is_cyclical:
            validation_errors["NoLoops"] = "Cycle in Influence diagram detected."

        self._reconstruct_for_longest_node_path()

        # Check for options/outcomes for issues
        for issue in self.issues:
            if issue.type == Type.UNCERTAINTY:
                if issue.uncertainty is None or len(issue.uncertainty.outcomes) == 0:
                    validation_errors["UncertaintyOutcomes"] = (
                        f"No Outcomes found for Uncertainty {issue.name}."
                    )

            if issue.type == Type.DECISION:
                if issue.decision is None or len(issue.decision.options) == 0:
                    validation_errors["DecisionOptions"] = (
                        f"No Options found for Decision {issue.name}."
                    )

        # If there are any validation errors, raise a ValueError
        if validation_errors:
            raise ValueError(json.dumps(validation_errors))

    def traverse_graph_paths(self):
        paths: dict[uuid.UUID, set[uuid.UUID]] = {}
        for start_node in self.start_nodes:
            path = self.graph.DFS(start_node)
            paths[start_node] = path

        return paths

    def find_seperated_graphs(self) -> list[set[uuid.UUID]]:
        paths = self.traverse_graph_paths()
        seperated_graphs: list[set[uuid.UUID]] = []

        seperated_graphs = [path for path in paths.values()]

        seperated_graphs = join_sets_with_common_elements(seperated_graphs)

        return seperated_graphs
