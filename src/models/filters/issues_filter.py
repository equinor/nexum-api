import uuid
from typing import Optional
from src.models.project import Project
from src.models.filters.base_filter import BaseFilter
from src.models import (
    Issue,
    Decision,
    Uncertainty,
)
from src.constants import Type
from sqlalchemy.sql import ColumnElement
from sqlalchemy import or_


class IssueFilter(BaseFilter):
    issue_ids: Optional[list[uuid.UUID]] = None
    project_ids: Optional[list[uuid.UUID]] = None
    types: Optional[list[str]] = None
    names: Optional[list[str]] = None
    descriptions: Optional[list[str]] = None
    boundaries: Optional[list[str]] = None
    orders: Optional[list[int]] = None
    decision_types: Optional[list[str]] = None
    is_key_uncertainties: Optional[list[bool]] = None

    def construct_filters(self) -> list[ColumnElement[bool]]:
        # Initialize a list to hold all conditions
        conditions: list[ColumnElement[bool]] = []

        # Add conditions for each attribute
        self.add_condition_for_property(self.issue_ids, self._issue_id_condition, conditions)
        self.add_condition_for_property(self.project_ids, self._project_id_condition, conditions)
        self.add_condition_for_property(self.types, self._type_condition, conditions)
        self.add_condition_for_property(self.names, self._name_condition, conditions)
        self.add_condition_for_property(self.descriptions, self._description_condition, conditions)
        self.add_condition_for_property(self.boundaries, self._boundary_condition, conditions)
        self.add_condition_for_property(self.orders, self._order_condition, conditions)
        self.add_condition_for_property(
            self.decision_types, self._decision_type_condition, conditions
        )
        self.add_condition_for_property(
            self.is_key_uncertainties, self._is_key_uncertainty, conditions
        )

        return conditions

    # Static helper methods to encapsulate condition logic
    @staticmethod
    def _issue_id_condition(issue_id: uuid.UUID) -> ColumnElement[bool]:
        return Issue.id == issue_id

    @staticmethod
    def _project_id_condition(project_id: uuid.UUID) -> ColumnElement[bool]:
        return Issue.project.has(Project.id == project_id)

    @staticmethod
    def _type_condition(issue_type: str) -> ColumnElement[bool]:
        return Issue.type == issue_type

    @staticmethod
    def _name_condition(name: str) -> ColumnElement[bool]:
        return Issue.name.ilike(f"%{name}%")

    @staticmethod
    def _description_condition(description: str) -> ColumnElement[bool]:
        return Issue.description.ilike(f"%{description}%")

    @staticmethod
    def _boundary_condition(boundary: str) -> ColumnElement[bool]:
        return Issue.boundary == boundary

    @staticmethod
    def _order_condition(order: int) -> ColumnElement[bool]:
        return Issue.order == order

    @staticmethod
    def _decision_type_condition(decision_type: str) -> ColumnElement[bool]:
        # Decision type is in issue.decision.type
        # Only applicable if issue.type is decision
        # For non-decision issues, this condition should be neutral (True)
        return or_(
            Issue.type != Type.DECISION.value,  # True for non-decision issues (ignore condition)
            Issue.decision.has(
                Decision.type == decision_type
            ),  # Check decision type for decision issues
        )

    @staticmethod
    def _is_key_uncertainty(is_key: bool) -> ColumnElement[bool]:
        # Uncertainty key status is in issue.uncertainty.is_key
        # Only applicable if issue.type is uncertainty
        # For non-uncertainty issues, this condition should be neutral (True)
        return or_(
            Issue.type
            != Type.UNCERTAINTY.value,  # True for non-uncertainty issues (ignore condition)
            Issue.uncertainty.has(
                Uncertainty.is_key == is_key
            ),  # Check is_key for uncertainty issues
        )
