from fastapi import APIRouter, Depends, status
from app.schemas.coaccion import RoboCoaccionCreate, RoboCoaccionResponse
from app.services.coaccion_service import CoaccionService
from app.api.deps import get_coaccion_service

router = APIRouter(prefix="/coaccion", tags=["Protocolo Silencioso"])

@router.post("/alertar/", response_model=RoboCoaccionResponse, status_code=status.HTTP_201_CREATED)
def alertar_robo_coaccion(
    data: RoboCoaccionCreate,
    coaccion_service: CoaccionService = Depends(get_coaccion_service)
):
    """
    Controlador para despacho de alertas de robo, asalto o coacción.
    Mantiene la discreción en el dispositivo y prioriza a la PNP.
    """
    return coaccion_service.despachar_robo_coaccion(data)
