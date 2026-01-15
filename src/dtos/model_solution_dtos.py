import uuid
from pydantic import BaseModel
from typing import List
from src.dtos.option_dtos import OptionOutgoingDto
from src.dtos.outcome_dtos import OutcomeOutgoingDto


class ParentState(BaseModel):
    parent_id: uuid.UUID
    state: OptionOutgoingDto|OutcomeOutgoingDto

class OptimalOption(BaseModel):
    parent_states: List[ParentState]
    decision_id: uuid.UUID
    state: OptionOutgoingDto

class DecisionSolution(BaseModel):
    optimal_decisions: List[OptimalOption]
    mean: float

class SolutionDto(BaseModel):
    decision_solutions: list[DecisionSolution]

    def get_all_optimal_decisions(self):
        a: List[OptimalOption] = []
        [a.extend(x.optimal_decisions) for x in self.decision_solutions]
        return a