from fastapi import APIRouter, Depends, status
from typing import List, Dict, Any
from app.schemas.family import FamiliarCreate, FamiliarResponse
from app.services.family_service import FamilyService
from app.api.deps import get_family_service

router = APIRouter(prefix="/familia", tags=["Red Familiar"])

@router.post("/agregar/", status_code=status.HTTP_201_CREATED)
def agregar_familiar(
    data: FamiliarCreate,
    family_service: FamilyService = Depends(get_family_service)
):
    """Controlador para vincular un familiar a la red de protección del usuario."""
    return family_service.agregar_familiar(data)

@router.get("/listar/{usuario_responsable}", response_model=List[FamiliarResponse])
def listar_familiares(
    usuario_responsable: str,
    family_service: FamilyService = Depends(get_family_service)
):
    """Controlador para listar miembros de la red de protección familiar."""
    return family_service.listar_familiares(usuario_responsable)
