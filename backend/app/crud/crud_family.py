# Wrapper de compatibilidad hacia atrás
from sqlalchemy.orm import Session
from typing import List
from app.models.family import RedFamiliar
from app.schemas.family import FamiliarCreate
from app.repositories.family_repository import FamilyRepository

def add_family_member(db: Session, familiar_in: FamiliarCreate) -> RedFamiliar:
    return FamilyRepository(db).add_member(
        usuario_responsable=familiar_in.usuario_responsable,
        nombre=familiar_in.nombre,
        parentesco=familiar_in.parentesco,
        dispositivo_id=familiar_in.dispositivo_id
    )

def get_family_by_responsible(db: Session, usuario_responsable: str) -> List[RedFamiliar]:
    return FamilyRepository(db).get_by_responsible(usuario_responsable)
