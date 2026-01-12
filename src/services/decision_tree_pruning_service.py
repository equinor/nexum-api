import uuid
from abc import ABC, abstractmethod
from typing import Optional, Set
from dataclasses import dataclass

from src.constants import Type
from src.services.pyagrum_solver import SolutionDto, OptimalOption
from src.services.decision_tree.decision_tree_creator import (
    DecisionTreeDTO, 
    EndPointNodeDto, 
    ProbabilityDto
)
from src.dtos.outcome_dtos import OutcomeOutgoingDto


@dataclass
class PruningContext:
    """Context object to hold state during tree traversal."""
    current_path: Set[uuid.UUID]
    solution: SolutionDto
    
    def add_to_path(self, node_id: uuid.UUID) -> None:
        """Add a node to the current path."""
        self.current_path.add(node_id)
    
    def remove_from_path(self, node_id: uuid.UUID) -> None:
        """Remove a node from the current path."""
        self.current_path.discard(node_id)
    
    def is_parent_valid(self, decision: OptimalOption) -> bool:
        """Check if all parent states are in the current path."""
        parent_ids = {state.state.id for state in decision.parent_states}
        return parent_ids.issubset(self.current_path)


class TreePruner(ABC):
    """Abstract base class for tree pruning visitors."""
    
    @abstractmethod
    def visit_decision_node(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """Visit and prune a decision node."""
        pass
    
    @abstractmethod
    def visit_uncertainty_node(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """Visit and prune an uncertainty node."""
        pass
    
    @abstractmethod
    def visit_endpoint_node(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """Visit an endpoint node."""
        pass
    
    def prune(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """Main entry point for pruning. Dispatches to appropriate visit method."""
        if isinstance(node.tree_node.issue, EndPointNodeDto):
            return self.visit_endpoint_node(node, context)
        
        if (node.tree_node.issue.type == Type.DECISION.value and 
            node.tree_node.issue.decision is not None and 
            node.children):
            return self.visit_decision_node(node, context)
        else:
            return self.visit_uncertainty_node(node, context)


class DecisionTreePruningException(Exception):
    """Custom exception for decision tree pruning errors."""
    pass


class OptimalDecisionTreePruner(TreePruner):
    
    def visit_endpoint_node(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """No action taken on endpoint nodes"""
        return node
    
    def visit_decision_node(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """Prune decision node to keep only the optimal option."""
        if (
            isinstance(node.tree_node.issue, EndPointNodeDto) or 
            not node.children or 
            not node.tree_node.issue.decision
        ):
            raise DecisionTreePruningException("Invalid decision node visited")
        
        optimal_decisions = context.solution.get_all_optimal_decisions()
        optimal_decision = self._find_optimal_decision(node, optimal_decisions, context)
        
        if optimal_decision is None:
            raise DecisionTreePruningException(
                f"No optimal decision found for node {node.tree_node.issue.name}"
            )
        
        # Find the index of the optimal option
        option_index = self._find_option_index(node, optimal_decision.state.id)
        
        # Prune to keep only the optimal path
        self._prune_decision_branches(node, option_index, optimal_decision.state.id)
        
        # Add decision to path and recurse
        context.add_to_path(optimal_decision.state.id)
        try:
            self.prune(node.children[0], context)
        finally:
            context.remove_from_path(optimal_decision.state.id)
        
        return node
    
    def visit_uncertainty_node(self, node: DecisionTreeDTO, context: PruningContext) -> Optional[DecisionTreeDTO]:
        """Process uncertainty node by filtering zero probabilities and recursing."""
        if (
            isinstance(node.tree_node.issue, EndPointNodeDto) or 
            not node.children or 
            not node.tree_node.issue.uncertainty
        ):
            raise DecisionTreePruningException("Invalid uncertainty node visited")
            
        self._align_probabilities_with_outcomes(node)
        self._remove_zero_probability_outcomes(node)

        
        # Recurse through all remaining outcomes
        child: DecisionTreeDTO
        outcome: OutcomeOutgoingDto
        for child, outcome in zip(
            node.children, 
            node.tree_node.issue.uncertainty.outcomes
        ):
            context.add_to_path(outcome.id)
            try:
                self.prune(child, context)
            finally:
                context.remove_from_path(outcome.id)
        
        return node
    
    def _find_optimal_decision(self, node: DecisionTreeDTO, optimal_decisions: list[OptimalOption], 
                             context: PruningContext) -> Optional[OptimalOption]:
        """Find the optimal decision for the current node given the current path."""
        for decision in optimal_decisions:
            if (decision.decision_id == node.tree_node.issue.id and 
                context.is_parent_valid(decision)):
                return decision
        return None
    
    def _find_option_index(self, node: DecisionTreeDTO, decision_state_id: uuid.UUID) -> int:
        """Find the index of the optimal option in the node's options list."""
        if (
            isinstance(node.tree_node.issue, EndPointNodeDto) or 
            not node.tree_node.issue.decision
        ):
            raise DecisionTreePruningException("Invalid decision node visited")
        
        option_ids = [option.id for option in node.tree_node.issue.decision.options]
        try:
            return option_ids.index(decision_state_id)
        except ValueError:
            raise DecisionTreePruningException(
                f"Optimal decision state {decision_state_id} not found in node options"
            )
    
    def _prune_decision_branches(self, node: DecisionTreeDTO, option_index: int, decision_state_id: uuid.UUID) -> None:
        """Remove non-optimal branches from the decision node."""
        if (
            isinstance(node.tree_node.issue, EndPointNodeDto) or 
            not node.children or 
            not node.tree_node.issue.decision
        ):
            raise DecisionTreePruningException("Invalid decision node visited")
        
        node.children = [node.children[option_index]]
        
        node.tree_node.issue.decision.options = [
            option for option in node.tree_node.issue.decision.options 
            if option.id == decision_state_id
        ]

    @staticmethod
    def _align_probabilities_with_outcomes(node: DecisionTreeDTO) -> None:
        """Sort probabilities to match the order of outcomes."""
        if (
            isinstance(node.tree_node.issue, EndPointNodeDto) or 
            not node.tree_node.issue.uncertainty or
            not node.tree_node.probabilities
        ):
            raise DecisionTreePruningException("Invalid uncertainty node visited")
        
        outcome_order = {
            outcome.id: i 
            for i, outcome in enumerate(node.tree_node.issue.uncertainty.outcomes)
        }
        node.tree_node.probabilities.sort(
            key=lambda prob: outcome_order.get(prob.outcome_id, float('inf'))
        )
    
    def _remove_zero_probability_outcomes(self, node: DecisionTreeDTO) -> None:
        """Remove outcomes with zero probability."""
        if (
            isinstance(node.tree_node.issue, EndPointNodeDto) or 
            not node.children or
            not node.tree_node.issue.uncertainty or
            not node.tree_node.probabilities
        ):
            raise DecisionTreePruningException("Invalid uncertainty node visited")
        
        items_to_remove: list[
            tuple[DecisionTreeDTO, ProbabilityDto, OutcomeOutgoingDto]
        ]  = []

        child: DecisionTreeDTO
        prob: ProbabilityDto
        outcome: OutcomeOutgoingDto

        for child, prob, outcome in zip(
            node.children, 
            node.tree_node.probabilities, 
            node.tree_node.issue.uncertainty.outcomes
        ):
            if prob.probability_value == 0:
                items_to_remove.append((child, prob, outcome))
        
        # Remove zero probability items
        for child, prob, outcome in items_to_remove:
            node.children.remove(child)
            node.tree_node.probabilities.remove(prob)
            node.tree_node.issue.uncertainty.outcomes.remove(outcome)


class DecisionTreePruningService:
    """Service class that orchestrates the pruning process."""
    
    def __init__(self, pruner: TreePruner):
        self.pruner = pruner
    
    def prune_tree_for_optimal_decisions(self, tree_root: DecisionTreeDTO, solution: SolutionDto) -> Optional[DecisionTreeDTO]:
        """Main method to prune a decision tree for optimal decisions."""
        context = PruningContext(current_path=set(), solution=solution)
        return self.pruner.prune(tree_root, context)
    