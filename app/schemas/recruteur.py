from pydantic import BaseModel , validator
from typing import Optional , Literal
from app.schemas.utilisateur import UtilisateurBase, UtilisateurCreate, UtilisateurUpdate, Utilisateur
from app.schemas.entreprise import EntrepriseCreate

# class RecruteurBase(UtilisateurBase):
#     poste: str
#     entreprise_id: int

# class RecruteurCreate(UtilisateurCreate, RecruteurBase):
#     pass

# class RecruteurUpdate(UtilisateurUpdate):
#     poste: Optional[str] = None
#     entreprise_id: Optional[int] = None

# class Recruteur(Utilisateur, RecruteurBase):
#     class Config:
#         from_attributes = True

class RecruteurBase(UtilisateurBase):
    poste: str

class RecruteurUpdate(UtilisateurUpdate):
    poste: Optional[str] = None
    entreprise_id: Optional[int] = None

# class Recruteur(Utilisateur, RecruteurBase):
#     entreprise_id: int
    
#     class Config:
#         from_attributes = True

# CORRECTION: Schéma de réponse avec tous les champs
class Recruteur(Utilisateur):
    poste: str
    entreprise_id: int
    
    class Config:
        from_attributes = True

# NOUVEAU: Schéma pour l'inscription avec entreprise existante
class RecruteurCreateWithExistingEntreprise(UtilisateurCreate, RecruteurBase):
    entreprise_id: int

# NOUVEAU: Schéma pour l'inscription avec nouvelle entreprise
class RecruteurCreateWithNewEntreprise(UtilisateurCreate, RecruteurBase):
    entreprise: EntrepriseCreate

# NOUVEAU: Schéma unifié pour l'inscription
class RecruteurInscription(UtilisateurCreate, RecruteurBase):
    """Schéma pour l'inscription d'un recruteur."""
    mode_entreprise: Literal["existante", "nouvelle"]
    
    # Champs conditionnels selon le mode
    entreprise_id: Optional[int] = None  # Requis si mode_entreprise = "existante"
    entreprise: Optional[EntrepriseCreate] = None  # Requis si mode_entreprise = "nouvelle"
    
    @validator('entreprise_id')
    def validate_entreprise_id(cls, v, values):
        if values.get('mode_entreprise') == 'existante' and v is None:
            raise ValueError('entreprise_id est requis quand mode_entreprise = "existante"')
        if values.get('mode_entreprise') == 'nouvelle' and v is not None:
            raise ValueError('entreprise_id doit être None quand mode_entreprise = "nouvelle"')
        return v
    
    @validator('entreprise')
    def validate_entreprise(cls, v, values):
        if values.get('mode_entreprise') == 'nouvelle' and v is None:
            raise ValueError('entreprise est requis quand mode_entreprise = "nouvelle"')
        if values.get('mode_entreprise') == 'existante' and v is not None:
            raise ValueError('entreprise doit être None quand mode_entreprise = "existante"')
        return v