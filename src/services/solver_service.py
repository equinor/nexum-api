import uuid
import asyncio
from src.services.project_service import ProjectService
from src.services.pyagrum_solver import PyagrumSolver
from src.session_manager import sessionmanager
from concurrent.futures import ThreadPoolExecutor
from functools import partial

executor = ThreadPoolExecutor()


class SolverService:
    def __init__(
        self,
        project_service: ProjectService,
    ):
        self.project_service = project_service

    async def find_optimal_decision_pyagrum(self, project_id: uuid.UUID):
        async for session in sessionmanager.get_session():
            (
                issues,
                edges,
            ) = await self.project_service.get_influence_diagram_data(session, project_id)

            solution = PyagrumSolver().find_optimal_decisions(issues=issues, edges=edges)
            solution = await asyncio.get_event_loop().run_in_executor(
                executor,
                partial(
                    PyagrumSolver().find_optimal_decisions,
                    issues=issues,
                    edges=edges,
                ),
            )

            return solution
