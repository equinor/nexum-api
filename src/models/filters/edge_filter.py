from typing import Optional
import uuid
from src.models import (
    Edge,
    Node,
    Issue,
    Decision,
    Uncertainty,
)
from src.models.filters.base_filter import BaseFilter
from src.constants import Type
from sqlalchemy.sql import ColumnElement
from sqlalchemy import or_


class EdgeFilter(BaseFilter):
    ids: Optional[list[uuid.UUID]] = None
    issue_boundaries: Optional[list[str]] = None
    issue_types: Optional[list[str]] = None
    project_ids: Optional[list[uuid.UUID]] = None
    decision_types: Optional[list[str]] = None
    is_key_uncertainties: Optional[list[bool]] = None

    def construct_filters(self) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []

        self.add_condition_for_property(self.ids, self._id_condition, conditions)

        self.add_condition_for_property(
            self.issue_boundaries,
            self._tail_node_boundary_condition,
            conditions,
        )

        self.add_condition_for_property(
            self.issue_types, self._tail_node_issue_type_condition, conditions
        )

        self.add_condition_for_property(
            self.issue_boundaries,
            self._head_node_boundary_condition,
            conditions,
        )

        self.add_condition_for_property(
            self.issue_types, self._head_node_issue_type_condition, conditions
        )

        self.add_condition_for_property(
            self.decision_types, self._tail_node_decision_type_condition, conditions
        )

        self.add_condition_for_property(
            self.decision_types, self._head_node_decision_type_condition, conditions
        )

        self.add_condition_for_property(
            self.is_key_uncertainties, self._tail_node_is_key_uncertainty_condition, conditions
        )

        self.add_condition_for_property(
            self.is_key_uncertainties, self._head_node_is_key_uncertainty_condition, conditions
        )

        self.add_condition_for_property(self.project_ids, self._project_id_condition, conditions)

        return conditions

    # Static helper methods to encapsulate condition logic
    @staticmethod
    def _id_condition(id: uuid.UUID) -> ColumnElement[bool]:
        return Edge.id == id

    @staticmethod
    def _project_id_condition(project_id: uuid.UUID) -> ColumnElement[bool]:
        return Edge.project_id == project_id

    @staticmethod
    def _tail_node_boundary_condition(
        issue_boundary: str,
    ) -> ColumnElement[bool]:
        return Edge.tail_node.has(Node.issue.has(Issue.boundary == issue_boundary))

    @staticmethod
    def _tail_node_issue_type_condition(
        issue_type: str,
    ) -> ColumnElement[bool]:
        return Edge.tail_node.has(Node.issue.has(Issue.type == issue_type))

    @staticmethod
    def _head_node_boundary_condition(
        issue_boundary: str,
    ) -> ColumnElement[bool]:
        return Edge.head_node.has(Node.issue.has(Issue.boundary == issue_boundary))

    @staticmethod
    def _head_node_issue_type_condition(
        issue_type: str,
    ) -> ColumnElement[bool]:
        return Edge.head_node.has(Node.issue.has(Issue.type == issue_type))

    @staticmethod
    def _tail_node_decision_type_condition(
        decision_type: str,
    ) -> ColumnElement[bool]:
        # Decision type condition for tail node
        # Only applicable if tail node issue type is decision
        # For non-decision issues, this condition should be neutral (True)
        return or_(
            Edge.tail_node.has(
                Node.issue.has(Issue.type != Type.DECISION.value)
            ),  # True for non-decision issues
            Edge.tail_node.has(
                Node.issue.has(Issue.decision.has(Decision.type == decision_type))
            ),  # Check decision type
        )

    @staticmethod
    def _head_node_decision_type_condition(
        decision_type: str,
    ) -> ColumnElement[bool]:
        # Decision type condition for head node
        # Only applicable if head node issue type is decision
        # For non-decision issues, this condition should be neutral (True)
        return or_(
            Edge.head_node.has(
                Node.issue.has(Issue.type != Type.DECISION.value)
            ),  # True for non-decision issues
            Edge.head_node.has(
                Node.issue.has(Issue.decision.has(Decision.type == decision_type))
            ),  # Check decision type
        )

    @staticmethod
    def _tail_node_is_key_uncertainty_condition(
        is_key: bool,
    ) -> ColumnElement[bool]:
        # Uncertainty key status condition for tail node
        # Only applicable if tail node issue type is uncertainty
        # For non-uncertainty issues, this condition should be neutral (True)
        return or_(
            Edge.tail_node.has(
                Node.issue.has(Issue.type != Type.UNCERTAINTY.value)
            ),  # True for non-uncertainty issues
            Edge.tail_node.has(
                Node.issue.has(Issue.uncertainty.has(Uncertainty.is_key == is_key))
            ),  # Check is_key
        )

    @staticmethod
    def _head_node_is_key_uncertainty_condition(
        is_key: bool,
    ) -> ColumnElement[bool]:
        # Uncertainty key status condition for head node
        # Only applicable if head node issue type is uncertainty
        # For non-uncertainty issues, this condition should be neutral (True)
        return or_(
            Edge.head_node.has(
                Node.issue.has(Issue.type != Type.UNCERTAINTY.value)
            ),  # True for non-uncertainty issues
            Edge.head_node.has(
                Node.issue.has(Issue.uncertainty.has(Uncertainty.is_key == is_key))
            ),  # Check is_key
        )
