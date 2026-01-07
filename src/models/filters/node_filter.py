import uuid
from typing import Optional
from src.models.project import Project
from src.models.filters.base_filter import BaseFilter
from src.models import Node
from sqlalchemy.sql import ColumnElement


class NodeFilter(BaseFilter):
    node_ids: Optional[list[uuid.UUID]] = None
    issue_ids: Optional[list[uuid.UUID]] = None
    project_ids: Optional[list[uuid.UUID]] = None
    names: Optional[list[str]] = None

    def construct_filters(self) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        self.add_condition_for_property(self.node_ids, self._node_id_condition, conditions)
        self.add_condition_for_property(self.issue_ids, self._issue_id_condition, conditions)
        self.add_condition_for_property(self.project_ids, self._project_id_condition, conditions)
        self.add_condition_for_property(self.names, self._name_condition, conditions)
        return conditions

    # Static helper methods to encapsulate condition logic
    @staticmethod
    def _node_id_condition(node_id: uuid.UUID) -> ColumnElement[bool]:
        return Node.id == node_id

    @staticmethod
    def _issue_id_condition(issue_id: uuid.UUID) -> ColumnElement[bool]:
        return Node.issue_id == issue_id

    @staticmethod
    def _project_id_condition(project_id: uuid.UUID) -> ColumnElement[bool]:
        return Node.project.has(Project.id == project_id)

    @staticmethod
    def _name_condition(name: str) -> ColumnElement[bool]:
        return Node.name.ilike(f"%{name}%")
