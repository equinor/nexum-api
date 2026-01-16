from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.project_duplication_service import ProjectDuplicationService
from src.session_manager import sessionmanager
from sqlalchemy import create_engine, Engine
from src.services.project_role_service import ProjectRoleService
from src.services.decision_service import DecisionService
from src.services.project_service import ProjectService
from src.services.objective_service import ObjectiveService
from src.services.uncertainty_service import UncertaintyService
from src.services.discrete_probability_service import DiscreteProbabilityService
from src.services.discrete_utility_service import DiscreteUtilityService
from src.services.utility_service import UtilityService
from src.services.value_metric_service import ValueMetricService
from src.services.edge_service import EdgeService
from src.services.node_service import NodeService
from src.services.node_style_service import NodeStyleService
from src.services.issue_service import IssueService
from src.services.outcome_service import OutcomeService
from src.services.option_service import OptionService
from src.services.user_service import UserService
from src.services.solver_service import SolverService
from src.services.structure_service import StructureService
from src.config import config
from src.database import get_connection_string_and_token, build_connection_url


async def get_sync_engine(environment: str = config.APP_ENV) -> Engine:
    sync_engine: Engine | None = None
    db_connection_string, token_dict = await get_connection_string_and_token(environment)
    conn_str = build_connection_url(db_connection_string, driver="pyodbc")
    if token_dict and environment != "local":
        sync_engine = create_engine(conn_str, echo=False, connect_args={"attrs_before": token_dict})
    else:
        sync_engine = create_engine(conn_str, echo=False)
    assert sync_engine is not None
    return sync_engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in sessionmanager.get_session():
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e


async def get_project_service() -> ProjectService:
    return ProjectService()


async def get_project_duplication_service() -> ProjectDuplicationService:
    return ProjectDuplicationService()


async def get_project_role_service() -> ProjectRoleService:
    return ProjectRoleService()


async def get_decision_service() -> DecisionService:
    return DecisionService()


async def get_outcome_service() -> OutcomeService:
    return OutcomeService()


async def get_option_service() -> OptionService:
    return OptionService()


async def get_objective_service() -> ObjectiveService:
    return ObjectiveService()


async def get_uncertainty_service() -> UncertaintyService:
    return UncertaintyService()


async def get_discrete_probability_service() -> DiscreteProbabilityService:
    return DiscreteProbabilityService()


async def get_discrete_utility_service() -> DiscreteUtilityService:
    return DiscreteUtilityService()


async def get_utility_service() -> UtilityService:
    return UtilityService()


async def get_value_metric_service() -> ValueMetricService:
    return ValueMetricService()


async def get_edge_service() -> EdgeService:
    return EdgeService()


async def get_node_service() -> NodeService:
    return NodeService()


async def get_node_style_service() -> NodeStyleService:
    return NodeStyleService()


async def get_issue_service() -> IssueService:
    return IssueService()


async def get_user_service() -> UserService:
    return UserService()


async def get_solver_service() -> SolverService:
    return SolverService(await get_project_service())


async def get_structure_service() -> StructureService:
    return StructureService(await get_project_service())
