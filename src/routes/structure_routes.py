import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from src.services.structure_service import StructureService
from src.dependencies import get_structure_service
from src.dtos.decision_tree_dtos import DecisionTreeDTO, PartialOrderDTO


router = APIRouter(tags=["structure"])


@router.get("/structure/{project_id}/decision_tree")
async def get_decision_tree(
    project_id: uuid.UUID, structure_service: StructureService = Depends(get_structure_service)
) -> Optional[DecisionTreeDTO]:
    try:
        return await structure_service.create_decision_tree_dtos(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/structure/{project_id}/partial_order")
async def get_partial_order(
    project_id: uuid.UUID, structure_service: StructureService = Depends(get_structure_service)
) -> Optional[PartialOrderDTO]:
    try:
        return await structure_service.create_partial_order(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
