import uuid
import asyncio
from src.services.pyagrum_solver import PyagrumSolver
from src.services.scenario_service import ScenarioService
from src.session_manager import sessionmanager
from concurrent.futures import ThreadPoolExecutor
from functools import partial

executor = ThreadPoolExecutor()


class SolverService:
    def __init__(
        self,
        scenario_service: ScenarioService,
    ):
        self.scenario_service = scenario_service

    async def find_optimal_decision_pyagrum(self, scenario_id: uuid.UUID):
        async for session in sessionmanager.get_session():
            (
                issues,
                edges,
            ) = await self.scenario_service.get_influence_diagram_data(session, scenario_id)

        solution = await PyagrumSolver().find_optimal_decisions(issues=issues, edges=edges)

        return solution
