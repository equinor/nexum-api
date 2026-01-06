import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from src.dtos.issue_dtos import IssueOutgoingDto


class EdgeUUIDDto(BaseModel):
    tail: uuid.UUID
    head: uuid.UUID | None
    name: str = ""


class EndPointNodeDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    scenario_id: uuid.UUID
    type: str = "EndPoint"


class ProbabilityDto(BaseModel):
    outcome_name: str
    outcome_id: uuid.UUID
    probability_value: float
    discrete_probability_id: uuid.UUID

class UtilityDTDto(BaseModel):
    branch_name: str
    branch_id: uuid.UUID
    utility_value: float
    discrete_utility_id: Optional[uuid.UUID] = None   


class TreeNodeDto(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    issue: IssueOutgoingDto | EndPointNodeDto
    probabilities: Optional[list[ProbabilityDto]] = None
    utilities: Optional[list[UtilityDTDto]] = None

class DecisionTreeDTO(BaseModel):
    tree_node: TreeNodeDto
    children: Optional[List["DecisionTreeDTO"]] = None

class PartialOrderDTO(BaseModel):
    # list of issue ids
    issue_ids: Optional[List[uuid.UUID]] = None
