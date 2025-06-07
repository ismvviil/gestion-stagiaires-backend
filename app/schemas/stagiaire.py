from pydantic import BaseModel , EmailStr , validator
from typing import Optional
from app.schemas.utilisateur import UtilisateurBase, UtilisateurCreate, UtilisateurUpdate, Utilisateur
from datetime import date


class StagiaireBase(UtilisateurBase):
    photo: Optional[str] = None

class StagiaireCreate(UtilisateurCreate, StagiaireBase):
    pass

class StagiaireUpdate(UtilisateurUpdate):
    photo: Optional[str] = None

    # 🆕 NOUVEAUX CHAMPS MODIFIABLES
    telephone: Optional[str] = None
    date_naissance: Optional[date] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    niveau_etudes: Optional[str] = None
    specialite: Optional[str] = None
    cv_filename: Optional[str] = None
    competences_manuelles: Optional[str] = None  # Compétences saisies manuellement
    
    @validator('telephone')
    def validate_telephone(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('Le numéro de téléphone doit contenir au moins 10 chiffres')
        return v


class Stagiaire(Utilisateur, StagiaireBase):
    class Config:
        from_attributes = True  # pour permettre model_validate()


class StagiaireProfileUpdate(BaseModel):
    """Schéma spécifique pour la mise à jour du profil complet."""
    # Informations personnelles
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    date_naissance: Optional[date] = None

    # Adresse
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    
    # Formation et compétences
    niveau_etudes: Optional[str] = None
    specialite: Optional[str] = None
    competences_manuelles: Optional[str] = None
    
    # Photo de profil
    photo: Optional[str] = None

class StagiaireProfile(Utilisateur):
    """Schéma pour afficher le profil complet du stagiaire."""
    photo: Optional[str] = None
    telephone: Optional[str] = None
    date_naissance: Optional[date] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    niveau_etudes: Optional[str] = None
    specialite: Optional[str] = None
    cv_filename: Optional[str] = None
    competences_manuelles: Optional[str] = None
    competences_extraites: Optional[str] = None  # Compétences extraites du CV (future)
    
    class Config:
        from_attributes = True


class Stagiaire(Utilisateur, StagiaireBase):
    # 🆕 NOUVEAUX CHAMPS pour le modèle de base
    telephone: Optional[str] = None
    date_naissance: Optional[date] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    code_postal: Optional[str] = None
    niveau_etudes: Optional[str] = None
    specialite: Optional[str] = None
    cv_filename: Optional[str] = None
    competences_manuelles: Optional[str] = None
    competences_extraites: Optional[str] = None
    
    class Config:
        from_attributes = True