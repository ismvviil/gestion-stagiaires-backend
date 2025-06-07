from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from app.schemas.base import BaseSchema

class StatusCandidatureEnum(str, Enum):
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    ACCEPTEE = "acceptee"
    REFUSEE = "refusee"
    RETIREE = "retiree"

class CandidatureBase(BaseModel):
    lettre_motivation: Optional[str] = None
    competences: Optional[str] = None
    niveau_etudes: Optional[str] = None
    commentaires_candidat: Optional[str] = None
    offre_id: int

class CandidatureCreate(CandidatureBase):
    pass

class CandidatureUpdate(BaseModel):
    lettre_motivation: Optional[str] = None
    competences: Optional[str] = None
    niveau_etudes: Optional[str] = None
    commentaires_candidat: Optional[str] = None
    commentaires_recruteur: Optional[str] = None
    note_recruteur: Optional[int] = Field(None, ge=1, le=10)

class CandidatureResponse(CandidatureBase, BaseSchema):
    cv: Optional[str] = None
    status: StatusCandidatureEnum
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None
    stagiaire_id: int
    recruteur_id: Optional[int] = None
    commentaires_recruteur: Optional[str] = None
    note_recruteur: Optional[int] = None
    
    # offre: Optional[dict] = None  # Simple dict pour contenir les données de l'offre

    class Config:
        from_attributes = True

class CandidatureTraitement(BaseModel):
    action: str = Field(..., pattern="^(accepter|refuser|en_cours)$")
    commentaires: Optional[str] = None
    note: Optional[int] = Field(None, ge=1, le=10)



