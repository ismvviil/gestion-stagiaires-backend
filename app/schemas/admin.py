from pydantic import BaseModel
from typing import Optional
from app.schemas.utilisateur import UtilisateurBase, UtilisateurCreate, UtilisateurUpdate, Utilisateur

class AdminBase(UtilisateurBase):
    niveau_acces: Optional[str] = "super_admin"

class AdminCreate(UtilisateurCreate, AdminBase):
    pass

class AdminUpdate(UtilisateurUpdate):
    niveau_acces: Optional[str] = None

class Admin(Utilisateur, AdminBase):
    class Config:
        from_attributes = True