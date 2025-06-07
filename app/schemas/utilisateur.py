from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from app.schemas.base import BaseSchema

# Schéma de base pour tous les types d'utilisateurs
class UtilisateurBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str
    actif: Optional[bool] = True

# Schéma pour la création d'un utilisateur
class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str
    
# Schéma pour la mise à jour d'un utilisateur
class UtilisateurUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    mot_de_passe: Optional[str] = None
    actif: Optional[bool] = None

# Schéma pour l'affichage d'un utilisateur (sans mot de passe)
class Utilisateur(UtilisateurBase, BaseSchema):
    type: str
    
    class Config:
        from_attributes = True

# Schéma pour l'authentification
class UtilisateurAuth(BaseModel):
    email: EmailStr
    mot_de_passe: str