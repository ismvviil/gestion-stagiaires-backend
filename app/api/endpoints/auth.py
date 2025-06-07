from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.utilisateur import Utilisateur
from app.models.role import Role
from app.models.entreprise import Entreprise
from app.models.recruteur import Recruteur 
from app.models.responsable_rh import ResponsableRH
from app.models.stagiaire import Stagiaire
from app.schemas.auth import Token
from app.schemas.utilisateur import UtilisateurCreate, Utilisateur as UtilisateurSchema
# from app.schemas.recruteur import RecruteurCreate
# 🆕 IMPORTS MIS À JOUR pour les recruteurs
from app.schemas.recruteur import (
    RecruteurInscription,  # Nouveau schéma principal
    RecruteurCreateWithExistingEntreprise,  # Optionnel
    RecruteurCreateWithNewEntreprise        # Optionnel,
    
)
from app.schemas.recruteur import Recruteur as RecruteurSchema

from app.schemas.responsable_rh import ResponsableRHCreate
from app.schemas.stagiaire import StagiaireCreate
from typing import Any
# from app.schemas.recruteur import RecruteurInscription

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """Obtenir un token d'accès pour l'authentification future."""
    # Debug - afficher les données reçues
    print(f"Tentative de connexion avec: {form_data.username}")
    
    # Recherche de l'utilisateur par email
    user = db.query(Utilisateur).filter(Utilisateur.email == form_data.username).first()
    
    # Vérification que l'utilisateur existe
    if user is None:
        print("Utilisateur non trouvé")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérification du mot de passe
    if not verify_password(form_data.password, user.mot_de_passe):
        print("Mot de passe incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérification que l'utilisateur est actif
    if not user.actif:
        print("Utilisateur inactif")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Utilisateur inactif"
        )
    
    # Création du token d'accès
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        user.email, expires_delta=access_token_expires
    )
    
    print(f"Connexion réussie pour: {user.email}")
    return {
        "access_token": token,
        "token_type": "bearer",
    }



@router.post("/register/recruteur", response_model=RecruteurSchema)
def register_recruteur(
    *, db: Session = Depends(get_db), recruteur_in: RecruteurInscription
) -> Any:
    """Enregistrer un nouveau recruteur avec entreprise existante ou nouvelle."""
    
    print(f"📝 Inscription recruteur: {recruteur_in.email}")
    print(f"🏢 Mode entreprise: {recruteur_in.mode_entreprise}")
    
    # Vérification que l'email n'est pas déjà utilisé
    user = db.query(Utilisateur).filter(Utilisateur.email == recruteur_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )
    
    entreprise_id = None
    
    # LOGIQUE SELON LE MODE
    if recruteur_in.mode_entreprise == "existante":
        print(f"🔍 Vérification entreprise existante ID: {recruteur_in.entreprise_id}")
        
        # Vérifier que l'entreprise existe
        entreprise = db.query(Entreprise).filter(Entreprise.id == recruteur_in.entreprise_id).first()
        if not entreprise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entreprise non trouvée"
            )
        
        entreprise_id = entreprise.id
        print(f"✅ Entreprise trouvée: {entreprise.raison_social}")
        
    elif recruteur_in.mode_entreprise == "nouvelle":
        print(f"🏗️ Création nouvelle entreprise: {recruteur_in.entreprise.raison_social}")
        
        # Vérifier que l'entreprise n'existe pas déjà (nom exact)
        existing_entreprise = db.query(Entreprise).filter(
            func.lower(Entreprise.raison_social) == func.lower(recruteur_in.entreprise.raison_social.strip())
        ).first()
        
        if existing_entreprise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Une entreprise avec la raison sociale '{recruteur_in.entreprise.raison_social}' existe déjà. "
                       f"Veuillez la sélectionner dans la liste des entreprises existantes."
            )
        
        # Créer la nouvelle entreprise
        nouvelle_entreprise = Entreprise(
            raison_social=recruteur_in.entreprise.raison_social.strip(),
            secteur_activite=recruteur_in.entreprise.secteur_activite,
            description=recruteur_in.entreprise.description,
            adresse=recruteur_in.entreprise.adresse,
            ville=recruteur_in.entreprise.ville,
            code_postal=recruteur_in.entreprise.code_postal,
            pays=recruteur_in.entreprise.pays,
            telephone=recruteur_in.entreprise.telephone,
            site_web=recruteur_in.entreprise.site_web,
            taille_entreprise=recruteur_in.entreprise.taille_entreprise
        )
        
        db.add(nouvelle_entreprise)
        db.flush()  # Pour obtenir l'ID sans committer
        
        entreprise_id = nouvelle_entreprise.id
        print(f"✅ Nouvelle entreprise créée: ID {entreprise_id}")
    
    # Création du recruteur
    print(f"👤 Création du recruteur...")
    recruteur = Recruteur(
        email=recruteur_in.email,
        mot_de_passe=get_password_hash(recruteur_in.mot_de_passe),
        nom=recruteur_in.nom,
        prenom=recruteur_in.prenom,
        poste=recruteur_in.poste,
        entreprise_id=entreprise_id
    )
    
    db.add(recruteur)
    db.commit()
    db.refresh(recruteur)
    
    print(f"✅ Recruteur créé: ID {recruteur.id}, Poste: {recruteur.poste}, Entreprise: {recruteur.entreprise_id}")
    return recruteur

@router.post("/register/responsable-rh", response_model=UtilisateurSchema)
def register_responsable_rh(
    *, db: Session = Depends(get_db), responsable_in: ResponsableRHCreate
) -> Any:
    """Enregistrer un nouveau responsable RH."""
    # Vérification que l'email n'est pas déjà utilisé
    user = db.query(Utilisateur).filter(Utilisateur.email == responsable_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )
    
    # Vérification que l'entreprise existe
    entreprise = db.query(Entreprise).filter(Entreprise.id == responsable_in.entreprise_id).first()
    if not entreprise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entreprise non trouvée"
        )
    
    # Création du responsable RH
    responsable = ResponsableRH(
        email=responsable_in.email,
        mot_de_passe=get_password_hash(responsable_in.mot_de_passe),
        nom=responsable_in.nom,
        prenom=responsable_in.prenom,
        poste=responsable_in.poste,
        entreprise_id=responsable_in.entreprise_id
    )
    db.add(responsable)
    db.commit()
    db.refresh(responsable)
    return responsable



# Dans app/api/endpoints/auth.py - Modifiez seulement cette fonction
@router.post("/register/stagiaire", response_model=UtilisateurSchema)
def register_stagiaire(
    *, db: Session = Depends(get_db), stagiaire_in: StagiaireCreate
) -> Any:
    """Enregistrer un nouveau stagiaire."""
    # Vérification que l'email n'est pas déjà utilisé
    user = db.query(Utilisateur).filter(Utilisateur.email == stagiaire_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )
    
    # CORRECTION: Gestion de la photo
    photo_filename = None
    if stagiaire_in.photo:
        # Si une photo est fournie, la valider
        if stagiaire_in.photo.startswith(("photos/", "uploads/")):
            photo_filename = stagiaire_in.photo
        elif stagiaire_in.photo != "1736375619848.jpg":  # Ignorer l'ancienne photo de test
            photo_filename = stagiaire_in.photo
        # Sinon, laisser None pour afficher les initiales
    
    print(f"📸 Inscription stagiaire - Photo: {photo_filename}")
    
    # Création du stagiaire
    stagiaire = Stagiaire(
        email=stagiaire_in.email,
        mot_de_passe=get_password_hash(stagiaire_in.mot_de_passe),
        nom=stagiaire_in.nom,
        prenom=stagiaire_in.prenom,
        photo=photo_filename  # Sera None si pas de vraie photo
    )
    db.add(stagiaire)
    db.commit()
    db.refresh(stagiaire)
    return stagiaire




# Ajouter cet import en haut du fichier auth.py
from app.models.admin import Admin
from app.schemas.admin import AdminCreate
from app.schemas.admin import Admin as AdminSchema

# Ajouter cette route dans le router auth.py
@router.post("/register/admin", response_model=AdminSchema)
def register_admin(
    *, db: Session = Depends(get_db), admin_in: AdminCreate
) -> Any:
    """Enregistrer un nouveau admin (pour le développement seulement)."""
    
    # Vérification que l'email n'est pas déjà utilisé
    user = db.query(Utilisateur).filter(Utilisateur.email == admin_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé."
        )
    
    # Création de l'admin
    admin = Admin(
        email=admin_in.email,
        mot_de_passe=get_password_hash(admin_in.mot_de_passe),
        nom=admin_in.nom,
        prenom=admin_in.prenom,
        niveau_acces=admin_in.niveau_acces
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin



# @router.post("/register/stagiaire", response_model=UtilisateurSchema)
# def register_stagiaire(
#     *, db: Session = Depends(get_db), stagiaire_in: StagiaireCreate
# ) -> Any:
#     """Enregistrer un nouveau stagiaire."""
#     # Vérification que l'email n'est pas déjà utilisé
#     user = db.query(Utilisateur).filter(Utilisateur.email == stagiaire_in.email).first()
#     if user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cet email est déjà utilisé."
#         )
    
#     # Création du stagiaire
#     stagiaire = Stagiaire(
#         email=stagiaire_in.email,
#         mot_de_passe=get_password_hash(stagiaire_in.mot_de_passe),
#         nom=stagiaire_in.nom,
#         prenom=stagiaire_in.prenom,
#         photo=stagiaire_in.photo
#     )
#     db.add(stagiaire)
#     db.commit()
#     db.refresh(stagiaire)
#     return stagiaire

# @router.post("/register/recruteur", response_model=UtilisateurSchema)
# def register_recruteur(
#     *, db: Session = Depends(get_db), recruteur_in: RecruteurCreate
# ) -> Any:
#     """Enregistrer un nouveau recruteur."""
#     # Vérification que l'email n'est pas déjà utilisé
#     user = db.query(Utilisateur).filter(Utilisateur.email == recruteur_in.email).first()
#     if user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Cet email est déjà utilisé."
#         )
    
#     # Vérification que l'entreprise existe
#     entreprise = db.query(Entreprise).filter(Entreprise.id == recruteur_in.entreprise_id).first()
#     if not entreprise:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Entreprise non trouvée"
#         )
    
#     # Création du recruteur
#     recruteur = Recruteur(
#         email=recruteur_in.email,
#         mot_de_passe=get_password_hash(recruteur_in.mot_de_passe),
#         nom=recruteur_in.nom,
#         prenom=recruteur_in.prenom,
#         poste=recruteur_in.poste,
#         entreprise_id=recruteur_in.entreprise_id
#     )
#     db.add(recruteur)
#     db.commit()
#     db.refresh(recruteur)
#     return recruteur
