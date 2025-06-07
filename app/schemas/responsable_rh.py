from pydantic import BaseModel
from typing import Optional
from app.schemas.utilisateur import UtilisateurBase, UtilisateurCreate, UtilisateurUpdate, Utilisateur

class ResponsableRHBase(UtilisateurBase):
    poste: str
    entreprise_id: int

class ResponsableRHCreate(UtilisateurCreate, ResponsableRHBase):
    pass

class ResponsableRHUpdate(UtilisateurUpdate):
    poste: Optional[str] = None
    entreprise_id: Optional[int] = None

class ResponsableRH(Utilisateur, ResponsableRHBase):
    class Config:
        from_attributes = True