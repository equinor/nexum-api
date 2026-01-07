import uuid
from fastapi import APIRouter, Depends, HTTPException
from src.services.solver_service import SolverService
from src.dependencies import get_solver_service

router = APIRouter(tags=["solvers"])


@router.get("/solvers/project/{project_id}")
async def get_optimal_decisions_for_project(
    project_id: uuid.UUID,
    solver_service: SolverService = Depends(get_solver_service),
):
    try:
        return await solver_service.find_optimal_decision_pyagrum(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
