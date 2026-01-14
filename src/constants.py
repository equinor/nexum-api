import uuid
from enum import Enum


class DisableSessionEvent(str, Enum):
    IS_EVENT_DISABLED = "is_session_disabled"


class Type(str, Enum):
    UNASSIGNED = "Unassigned"
    DECISION = "Decision"
    UNCERTAINTY = "Uncertainty"
    FACT = "Fact"
    UTILITY = "Utility"


class ObjectiveTypes(str, Enum):
    STRATEGIC = "Strategic"
    FUNDAMENTAL = "Fundamental"
    MEAN = "Mean"


class DepricatedIssueTypes(str, Enum):
    VALUE_METRIC = "Value Metric"
    UNDECIDED = "Undecided"
    OTHER = "Other"
    ACTION_ITEM = "Action Item"


class ProjectRoleType(str, Enum):
    DECISIONMAKER = "Decision Maker"
    FACILITATOR = "Facilitator"
    MEMBER = "Member"


class Boundary(str, Enum):
    IN = "in"
    ON = "on"
    OUT = "out"


class DecisionHierarchy(str, Enum):
    POLICY = "Policy"
    FOCUS = "Focus"
    TACTICAL = "Tactical"


class DatabaseConstants(int, Enum):
    MAX_SHORT_STRING_LENGTH = 60
    MAX_LONG_STRING_LENGTH = 600
    FLOAT_PRECISION = 53


class DtoConstants(int, Enum):
    DECIMAL_PLACES = 14


class NodeStates(str, Enum):
    OPTION = "option"
    OUTCOME = "outcome"


class SwaggerDocumentationConstants:
    FILTER_DOC = """
    filter: str (Optional)
        String for applying OData filtering.

        Documentation on the OData protocol can be found at:
        - [OData Query Options Overview]
        (https://learn.microsoft.com/en-us/odata/concepts/queryoptions-overview)
        - [odata-query Python Library](https://pypi.org/project/odata-query/) (Note: May differ
          from Microsoft's implementation)

        To filter on properties of related tables, use the following syntax:
        `related_table/property <operator> <value>`

        Example:
        - To find the issue where the node name is "Decision 1":
        `node/name eq 'Decision 1'`

        Supported operators include (but are not limited to):
        - `eq` (equals)
        - `ne` (not equals)
        - `gt` (greater than)
        - `lt` (less than)
        - `ge` (greater than or equal to)
        - `le` (less than or equal to)

        Notes:
        - This parameter is optional. If no filter is provided, all entities will be returned.
"""


class PageSize:
    DEFAULT: int = 1000000


default_value_metric_id = uuid.uuid5(uuid.NAMESPACE_DNS, "default value metric")
