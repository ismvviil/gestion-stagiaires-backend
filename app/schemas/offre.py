from pydantic import BaseModel, Field , ConfigDict
from typing import Optional, List
from datetime import date
from app.schemas.base import BaseSchema
from app.schemas.entreprise import Entreprise
from datetime import datetime, date


class OffreBase(BaseModel):
    """Schéma de base pour les offres de stage."""
    titre: str
    description: str
    type_stage: str
    remuneration: Optional[int] = None
    localisation: Optional[str] = None
    secteur: str
    date_debut: date
    date_fin: date
    competences_requises: Optional[str] = None
    est_active: bool = True

    model_config = ConfigDict(from_attributes=True)

class OffreCreate(OffreBase):
    """Schéma pour la création d'une offre."""
    entreprise_id: int

    model_config = ConfigDict(from_attributes=True)

class OffreUpdate(BaseModel):
    """Schéma pour la mise à jour d'une offre."""
    titre: Optional[str] = None
    description: Optional[str] = None
    type_stage: Optional[str] = None
    remuneration: Optional[int] = None
    localisation: Optional[str] = None
    secteur: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    competences_requises: Optional[str] = None
    est_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)

class OffreInDB(OffreBase):
    """Schéma pour une offre en base de données."""
    id: int
    entreprise_id: int
    recruteur_id: int

    model_config = ConfigDict(from_attributes=True)

class Offre(OffreInDB):
    """Schéma pour l'affichage d'une offre."""
    entreprise: Optional["Entreprise"] = None  # Assure-toi que Entreprise est défini
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class OffreSearchResult(BaseModel):
    """Schéma pour les résultats de recherche d'offres."""
    total: int
    offres: List[Offre]

    model_config = ConfigDict(from_attributes=True)
