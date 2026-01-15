from typing import Optional
import uuid
from src.models.objective import Objective
from src.models.filters.base_filter import BaseFilter
from sqlalchemy.sql import ColumnElement


class ObjectiveFilter(BaseFilter):
    ids: Optional[list[uuid.UUID]] = None
    project_ids: Optional[list[uuid.UUID]] = None

    def construct_filters(self) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []

        self.add_condition_for_property(self.ids, self._objective_id_condition, conditions)
        self.add_condition_for_property(self.project_ids, self._project_id_condition, conditions)

        return conditions

    @staticmethod
    def _project_id_condition(project_id: uuid.UUID) -> ColumnElement[bool]:
        return Objective.project_id == project_id

    @staticmethod
    def _objective_id_condition(objective_id: uuid.UUID) -> ColumnElement[bool]:
        return Objective.id == objective_id
