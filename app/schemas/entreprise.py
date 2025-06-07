from pydantic import BaseModel, ConfigDict, HttpUrl, validator
from typing import Optional
from app.schemas.base import BaseSchema

class EntrepriseBase(BaseModel):
    raison_social: str
    secteur_activite: str
    description: Optional[str] = None

    # """"""################""
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: Optional[str] = "France"
    telephone: Optional[str] = None
    site_web: Optional[str] = None
    taille_entreprise: Optional[str] = None

    @validator('taille_entreprise')
    def validate_taille_entreprise(cls, v):
        if v is not None:
            allowed_values = ["1-10", "11-50", "51-200", "200+"]
            if v not in allowed_values:
                raise ValueError(f"Taille entreprise doit être une des valeurs: {allowed_values}")
        return v

class EntrepriseCreate(EntrepriseBase):
    pass

class EntrepriseUpdate(BaseModel):
    raison_social: Optional[str] = None
    secteur_activite: Optional[str] = None
    description: Optional[str] = None

    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    pays: Optional[str] = None
    telephone: Optional[str] = None
    site_web: Optional[str] = None
    taille_entreprise: Optional[str] = None

class EntrepriseSearch(BaseModel):
    """Schéma pour la recherche d'entreprises."""
    raison_social: str

    
class Entreprise(EntrepriseBase, BaseSchema):
    model_config = ConfigDict(from_attributes=True)
