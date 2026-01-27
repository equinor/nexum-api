from typing import Optional
import uuid
from src.models.strategy import Strategy
from src.models.filters.base_filter import BaseFilter
from sqlalchemy.sql import ColumnElement


class StrategyFilter(BaseFilter):
    ids: Optional[list[uuid.UUID]] = None
    project_ids: Optional[list[uuid.UUID]] = None

    def construct_filters(self) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []

        self.add_condition_for_property(self.ids, self._strategy_id_condition, conditions)
        self.add_condition_for_property(self.project_ids, self._project_id_condition, conditions)

        return conditions

    @staticmethod
    def _project_id_condition(project_id: uuid.UUID) -> ColumnElement[bool]:
        return Strategy.project_id == project_id

    @staticmethod
    def _strategy_id_condition(strategy_id: uuid.UUID) -> ColumnElement[bool]:
        return Strategy.id == strategy_id
