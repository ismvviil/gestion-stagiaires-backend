from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from app.schemas.base import BaseSchema

class StatusMissionEnum(str, Enum):
    A_FAIRE = "a_faire"
    EN_COURS = "en_cours"
    EN_REVISION = "en_revision"
    TERMINEE = "terminee"
    ANNULEE = "annulee"

class PrioriteMissionEnum(str, Enum):
    BASSE = "basse"
    NORMALE = "normale"
    HAUTE = "haute"
    URGENTE = "urgente"

class MissionBase(BaseModel):
    titre: str
    description: str
    objectifs: Optional[str] = None
    date_debut_prevue: Optional[datetime] = None
    date_fin_prevue: Optional[datetime] = None
    priorite: PrioriteMissionEnum = PrioriteMissionEnum.NORMALE
    ressources_necessaires: Optional[str] = None
    livrables_attendus: Optional[str] = None

class MissionCreate(MissionBase):
    stage_id: int

class MissionUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    objectifs: Optional[str] = None
    date_debut_prevue: Optional[datetime] = None
    date_fin_prevue: Optional[datetime] = None
    priorite: Optional[PrioriteMissionEnum] = None
    status: Optional[StatusMissionEnum] = None
    pourcentage_completion: Optional[int] = Field(None, ge=0, le=100)
    ressources_necessaires: Optional[str] = None
    outils_utilises: Optional[str] = None
    livrables_attendus: Optional[str] = None
    livrables_fournis: Optional[str] = None
    feedback_stagiaire: Optional[str] = None

class MissionResponse(MissionBase, BaseSchema):
    status: StatusMissionEnum
    date_assignation: datetime
    date_debut_reel: Optional[datetime] = None
    date_fin_reel: Optional[datetime] = None
    pourcentage_completion: int
    outils_utilises: Optional[str] = None
    note_mission: Optional[int] = None
    feedback_recruteur: Optional[str] = None
    feedback_stagiaire: Optional[str] = None
    livrables_fournis: Optional[str] = None
    stage_id: int
    assigne_par_id: int
    
    class Config:
        from_attributes = True

class MissionAction(BaseModel):
    action: str = Field(..., pattern="^(commencer|soumettre|valider|rejeter|annuler)$")
    pourcentage: Optional[int] = Field(None, ge=0, le=100)
    note: Optional[int] = Field(None, ge=0, le=20)
    feedback: Optional[str] = None
    livrables: Optional[str] = None