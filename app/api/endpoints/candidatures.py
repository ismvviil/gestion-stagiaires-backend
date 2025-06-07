from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse
from app.core.file_storage import save_cv_file, delete_file
import os

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.candidature import Candidature, StatusCandidature
from app.models.offre import Offre
from app.models.utilisateur import Utilisateur
from app.schemas.candidature import (
    CandidatureCreate, CandidatureResponse, CandidatureTraitement
)

from app.core.file_storage import save_cv_file
from sqlalchemy.orm import joinedload

from app.models.stage import Stage

router = APIRouter()

@router.post("/", response_model=CandidatureResponse)
async def create_candidature(
    *,
    db: Session = Depends(get_db),
    candidature_in: CandidatureCreate,
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Créer une nouvelle candidature (stagiaires seulement)."""
    # Vérifier que l'offre existe et est active
    offre = db.query(Offre).filter(Offre.id == candidature_in.offre_id).first()
    if not offre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offre non trouvée"
        )
    if not offre.est_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette offre n'est plus active"
        )
    # Vérifier si le stagiaire n'a pas déjà postulé
    existing = db.query(Candidature).filter(
        Candidature.stagiaire_id == current_user.id,
        Candidature.offre_id == candidature_in.offre_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous avez déjà postulé à cette offre"
        )
    
    # Créer la candidature
    candidature = Candidature(
        **candidature_in.dict(),
        stagiaire_id=current_user.id
    )

    db.add(candidature)
    db.commit()
    db.refresh(candidature)
    return candidature

# @router.get("/mes-candidatures", response_model=List[CandidatureResponse])
# def get_mes_candidatures(
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_user_by_type("stagiaire")),
#     skip: int = 0,
#     limit: int = 100
# ):
#     """Récupérer les candidatures du stagiaire connecté."""
#     candidatures = db.query(Candidature).filter(
#         Candidature.stagiaire_id == current_user.id
#     ).offset(skip).limit(limit).all()
    
#     return candidatures
# Dans votre endpoint candidature.py

@router.get("/mes-candidatures")
def get_mes_candidatures(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire")),
    skip: int = 0,
    limit: int = 100
):
    """Récupérer les candidatures du stagiaire connecté."""
    candidatures = db.query(Candidature).options(
        joinedload(Candidature.offre).joinedload(Offre.entreprise)
    ).filter(
        Candidature.stagiaire_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    # Convertir manuellement en dictionnaire
    result = []
    for candidature in candidatures:
        candidature_dict = {
            "id": candidature.id,
            "cv": candidature.cv,
            "status": candidature.status.value if candidature.status else "en_attente",
            "date_debut": candidature.date_debut,
            "date_fin": candidature.date_fin,
            "stagiaire_id": candidature.stagiaire_id,
            "recruteur_id": candidature.recruteur_id,
            "lettre_motivation": candidature.lettre_motivation,
            "competences": candidature.competences,
            "niveau_etudes": candidature.niveau_etudes,
            "commentaires_candidat": candidature.commentaires_candidat,
            "commentaires_recruteur": candidature.commentaires_recruteur,
            "note_recruteur": candidature.note_recruteur,
            "offre_id": candidature.offre_id,
        }
        
        # Ajouter les infos de l'offre si elle existe
        if candidature.offre:
            candidature_dict["offre"] = {
                "id": candidature.offre.id,
                "titre": candidature.offre.titre,
                "localisation": candidature.offre.localisation,
                "secteur": candidature.offre.secteur,
                "est_active": candidature.offre.est_active,
                "entreprise": {
                    "id": candidature.offre.entreprise.id,
                    # CORRECTION ICI: utiliser raison_social au lieu de nom
                    "raison_social": candidature.offre.entreprise.raison_social
                } if candidature.offre.entreprise else None
            }
        else:
            candidature_dict["offre"] = None
            
        result.append(candidature_dict)
    
    return result

@router.put("/{candidature_id}/traiter", response_model=CandidatureResponse)
def traiter_candidature(
    *,
    db: Session = Depends(get_db),
    candidature_id: int,
    traitement: CandidatureTraitement,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """Traiter une candidature (recruteurs seulement)."""
    
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()
    if not candidature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidature non trouvée"
        )
    
    # Vérifier que le recruteur peut traiter cette candidature
    if candidature.offre.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à traiter cette candidature"
        )
    
     # Traiter selon l'action
    if traitement.action == "accepter":
        # Créer le stage automatiquement
        stage = candidature.accepter(current_user.id, traitement.commentaires)
        db.add(stage)  # Ajouter le stage à la session

    elif traitement.action == "refuser":
        candidature.refuser(current_user.id, traitement.commentaires)
    elif traitement.action == "en_cours":
        # ⚠️ MODIFICATION CRITIQUE - Passer les commentaires
        candidature.mettre_en_cours(current_user.id, traitement.commentaires) 

    if traitement.note:
        candidature.note_recruteur = traitement.note

    db.commit()
    db.refresh(candidature)
    return candidature

@router.post("/{candidature_id}/upload-cv")
async def upload_cv(
    *,
    candidature_id: int,
    cv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Upload CV pour une candidature."""
    candidature = db.query(Candidature).filter(
        Candidature.id == candidature_id,
        Candidature.stagiaire_id == current_user.id
    ).first()

    if not candidature:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    # Supprimer l'ancien CV s'il existe
    if candidature.cv:
        delete_file(candidature.cv)

    # Sauvegarder le nouveau CV
    cv_path = await save_cv_file(cv_file)
    candidature.cv = cv_path

    db.commit()
    return {"message": "CV uploadé avec succès", "cv_path": cv_path}

# @router.get("/recues", response_model=List[CandidatureResponse])
# def get_candidatures_recues(
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_user_by_type("recruteur")),
#     status_filter: Optional[str] = None,
#     offre_id: Optional[int] = None,
#     skip: int = 0,
#     limit: int = 100
# ):
#     """Récupérer les candidatures reçues par le recruteur."""
#     query = db.query(Candidature).join(Offre).filter(
#         Offre.recruteur_id == current_user.id
#     )

#     if status_filter:
#         query = query.filter(Candidature.status == status_filter)
#     if offre_id:
#         query = query.filter(Candidature.offre_id == offre_id)

#     candidatures = query.offset(skip).limit(limit).all()
#     return candidatures
# Dans votre fichier candidatures.py

# Dans votre fichier candidatures.py

from sqlalchemy.orm import joinedload

@router.get("/recues")  # Sans response_model
def get_candidatures_recues(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("recruteur")),
    status_filter: Optional[str] = None,
    offre_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Récupérer les candidatures reçues par le recruteur."""
    
    # Requête avec joinedload pour charger toutes les relations
    query = db.query(Candidature).options(
        joinedload(Candidature.offre).joinedload(Offre.entreprise),
        joinedload(Candidature.stagiaire)
    ).join(Offre).filter(
        Offre.recruteur_id == current_user.id
    )


    # CORRECTION: Convertir le status_filter en enum
    if status_filter:
        try:
            # Mapper les valeurs string vers les enum
            status_mapping = {
                "en_attente": StatusCandidature.EN_ATTENTE,
                "en_cours": StatusCandidature.EN_COURS, 
                "acceptee": StatusCandidature.ACCEPTEE,
                "refusee": StatusCandidature.REFUSEE,
                "retiree": StatusCandidature.RETIREE
            }
            
            if status_filter in status_mapping:
                enum_status = status_mapping[status_filter]
                query = query.filter(Candidature.status == enum_status)
            else:
                # Status invalide - ignorer le filtre ou lever une erreur
                print(f"Status invalide: {status_filter}")
        except Exception as e:
            print(f"Erreur conversion status: {e}")
            # Continuer sans filtre de status en cas d'erreur
    if offre_id:
        query = query.filter(Candidature.offre_id == offre_id)

    candidatures = query.offset(skip).limit(limit).all()
    
    # Convertir manuellement en dictionnaire
    result = []
    for candidature in candidatures:
        candidature_dict = {
            "id": candidature.id,
            "cv": candidature.cv,
            "status": candidature.status.value if candidature.status else "en_attente",
            "date_debut": candidature.date_debut,
            "date_fin": candidature.date_fin,
            "stagiaire_id": candidature.stagiaire_id,
            "recruteur_id": candidature.recruteur_id,
            "lettre_motivation": candidature.lettre_motivation,
            "competences": candidature.competences,
            "niveau_etudes": candidature.niveau_etudes,
            "commentaires_candidat": candidature.commentaires_candidat,
            "commentaires_recruteur": candidature.commentaires_recruteur,
            "note_recruteur": candidature.note_recruteur,
            "offre_id": candidature.offre_id,
        }
        
        # Ajouter les infos de l'offre
        if candidature.offre:
            candidature_dict["offre"] = {
                "id": candidature.offre.id,
                "titre": candidature.offre.titre,
                "localisation": candidature.offre.localisation,
                "secteur": candidature.offre.secteur,
                "est_active": candidature.offre.est_active,
                "entreprise": {
                    "id": candidature.offre.entreprise.id,
                    "raison_social": candidature.offre.entreprise.raison_social
                } if candidature.offre.entreprise else None
            }
        else:
            candidature_dict["offre"] = None
        
        # Ajouter les infos du stagiaire (basé sur votre modèle Utilisateur + Stagiaire)
        if candidature.stagiaire:
            candidature_dict["stagiaire"] = {
                "id": candidature.stagiaire.id,
                "email": candidature.stagiaire.email,
                "nom": candidature.stagiaire.nom,
                "prenom": candidature.stagiaire.prenom,
                # "telephone": getattr(candidature.stagiaire, 'telephone', None),
                "photo": candidature.stagiaire.photo,  # Champ spécifique au stagiaire
                # "date_naissance": getattr(candidature.stagiaire, 'date_naissance', None),
                # "adresse": getattr(candidature.stagiaire, 'adresse', None),
            }
        else:
            candidature_dict["stagiaire"] = None
            
        result.append(candidature_dict)
    
    return result
@router.get("/{candidature_id}/download-cv")
def download_cv(
    candidature_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Télécharger le CV d'une candidature."""
    candidature = db.query(Candidature).filter(Candidature.id == candidature_id).first()

    if not candidature or not candidature.cv:
        raise HTTPException(status_code=404, detail="CV non trouvé")
    
    # Vérifier les permissions
    if (current_user.type == "stagiaire" and candidature.stagiaire_id != current_user.id) or \
       (current_user.type == "recruteur" and candidature.offre.recruteur_id != current_user.id):
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    if not os.path.exists(candidature.cv):
        raise HTTPException(status_code=404, detail="Fichier CV non trouvé")
    
    return FileResponse(candidature.cv, filename=f"cv_candidature_{candidature_id}.pdf")

@router.delete("/{candidature_id}/retirer")
def retirer_candidature(
    candidature_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Permettre au stagiaire de retirer sa candidature."""
    candidature = db.query(Candidature).filter(
        Candidature.id == candidature_id,
        Candidature.stagiaire_id == current_user.id
    ).first()

    if not candidature:
        raise HTTPException(status_code=404, detail="Candidature non trouvée")
    
    if candidature.status in [StatusCandidature.ACCEPTEE, StatusCandidature.REFUSEE]:
        raise HTTPException(
            status_code=400, 
            detail="Impossible de retirer une candidature déjà traitée"
        )
    candidature.retirer()
    db.commit()
    
    return {"message": "Candidature retirée avec succès"}

