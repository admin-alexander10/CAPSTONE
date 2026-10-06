from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base_repository import BaseRepository
from app.domain.interfaces.repositories import IFamilyRepository
from app.models.family import RedFamiliar

class FamilyRepository(BaseRepository[RedFamiliar], IFamilyRepository):
    """Repositorio de la Red de Protección Familiar."""

    def __init__(self, db: Session):
        super().__init__(db, RedFamiliar)

    def get_by_responsible(self, usuario_responsable: str) -> List[RedFamiliar]:
        return self.db.query(RedFamiliar).filter(
            RedFamiliar.usuario_responsable == usuario_responsable
        ).all()

    def add_member(
        self,
        usuario_responsable: str,
        nombre: str,
        parentesco: str,
        dispositivo_id: Optional[str] = None
    ) -> RedFamiliar:
        nuevo_familiar = RedFamiliar(
            usuario_responsable=usuario_responsable,
            nombre=nombre,
            parentesco=parentesco,
            dispositivo_id=dispositivo_id or "DEV_DEFAULT"
        )
        return self.create(nuevo_familiar)
