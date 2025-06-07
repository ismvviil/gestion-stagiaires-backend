from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from app.schemas.base import BaseSchema

class StatusStageEnum(str, Enum):
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    INTERROMPU = "interrompu"
    SUSPENDU = "suspendu"

class StageBase(BaseModel):
    date_debut: datetime
    date_fin: datetime
    objectifs: Optional[str] = None
    description: Optional[str] = None

class StageCreate(StageBase):
    candidature_id: int
    stagiaire_id: int
    entreprise_id: int
    recruteur_id: int

class StageUpdate(BaseModel):
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    status: Optional[StatusStageEnum] = None
    objectifs: Optional[str] = None
    description: Optional[str] = None
    commentaires_entreprise: Optional[str] = None
    commentaires_stagiaire: Optional[str] = None
    note_finale: Optional[int] = Field(None, ge=0, le=20)

class StageResponse(StageBase, BaseSchema):
    status: StatusStageEnum
    date_debut_reel: Optional[datetime] = None
    date_fin_reel: Optional[datetime] = None
    commentaires_entreprise: Optional[str] = None
    commentaires_stagiaire: Optional[str] = None
    note_finale: Optional[int] = None
    certificat_genere: bool
    candidature_id: int
    stagiaire_id: int
    entreprise_id: int
    recruteur_id: int
    
    class Config:
        from_attributes = True

class StageAction(BaseModel):
    action: str = Field(..., pattern="^(commencer|terminer|interrompre|suspendre)$")
    commentaires: Optional[str] = None
    note_finale: Optional[int] = Field(None, ge=0, le=20)