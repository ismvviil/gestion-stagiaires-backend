# from fastapi import APIRouter, Depends
# from app.api.deps import get_current_user
# from app.models.utilisateur import Utilisateur

# # Import des schémas
# from app.schemas.utilisateur import Utilisateur as UtilisateurSchema
# from app.schemas.recruteur import Recruteur as RecruteurSchema
# from app.schemas.responsable_rh import ResponsableRH as ResponsableRHSchema
# from app.schemas.stagiaire import Stagiaire as StagiaireSchema

# router = APIRouter()

# @router.get("/me")
# def read_current_user(
#     current_user: Utilisateur = Depends(get_current_user)
# ):
#     """Récupérer les informations de l'utilisateur actuel."""

#     if current_user.type == "recruteur":
#         return RecruteurSchema.model_validate(current_user)
#     elif current_user.type == "responsable_rh":
#         return ResponsableRHSchema.model_validate(current_user)
#     elif current_user.type == "stagiaire":
#         return StagiaireSchema.model_validate(current_user)
#     else:
#         return UtilisateurSchema.model_validate(current_user)
# Dans votre fichier router users
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import Utilisateur as UtilisateurSchema
from app.schemas.recruteur import Recruteur as RecruteurSchema
from app.schemas.responsable_rh import ResponsableRH as ResponsableRHSchema
from app.schemas.stagiaire import Stagiaire as StagiaireSchema

router = APIRouter()

@router.get("/me")
def read_current_user(
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer les informations de l'utilisateur actuel."""
    
    # Debug détaillé pour les stagiaires
    if current_user.type == "stagiaire":
        print(f"=== DEBUG STAGIAIRE ===")
        print(f"Type de l'objet: {type(current_user)}")
        print(f"Attribut photo existe: {hasattr(current_user, 'photo')}")
        if hasattr(current_user, 'photo'):
            print(f"Valeur de la photo: {current_user.photo}")
        
        # Afficher tous les attributs disponibles
        print(f"Attributs disponibles: {[attr for attr in dir(current_user) if not attr.startswith('_')]}")
        
        # Créer le schéma et voir ce qui est inclus
        stagiaire_schema = StagiaireSchema.model_validate(current_user)
        print(f"Données du schéma: {stagiaire_schema.model_dump()}")
        
        return stagiaire_schema
    
    elif current_user.type == "recruteur":
        return RecruteurSchema.model_validate(current_user)
    elif current_user.type == "responsable_rh":
        return ResponsableRHSchema.model_validate(current_user)
    else:
        return UtilisateurSchema.model_validate(current_user)