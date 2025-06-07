from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.stage import Stage, StatusStage
from app.models.candidature import Candidature
from app.models.utilisateur import Utilisateur
from app.schemas.stage import (
    StageCreate, StageResponse, StageUpdate, StageAction
)
from sqlalchemy import text  # ← Ajoutez cet import

router = APIRouter()

# @router.get("/", response_model=List[StageResponse])
# def get_stages(
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_current_user),
#     skip: int = 0,
#     limit: int = 100,
#     status_filter: Optional[str] = None
# ):
#     # print("=== DEBUG ENUM VALUES ===")
#     # for status in StatusStage:
#     #     print(f"{status.name} = '{status.value}'")
    
#     # # DEBUG: Vérifier les données brutes de la DB
#     # raw_query = db.execute(text("SELECT status FROM stage LIMIT 5"))  # ← Utilisez text()
#     # print("=== DEBUG RAW DB VALUES ===")
#     # for row in raw_query:
#     #     print(f"DB value: '{row[0]}'")
    
    
#     query = db.query(Stage)

#     # Filtrer selon le type d'utilisateur
#     if current_user.type == "stagiaire":
#         query = query.filter(Stage.stagiaire_id == current_user.id)
#     elif current_user.type == "recruteur":
#         query = query.filter(Stage.recruteur_id == current_user.id)
#     elif current_user.type == "responsable_rh":
#         # Les RH peuvent voir tous les stages de leur entreprise
#         query = query.filter(Stage.entreprise_id == current_user.entreprise_id)

#     else:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Accès non autorisé"
#         )


#      # Filtre par statut si spécifié
#     if status_filter:
#         try:
#             status_mapping = {
#                 "en_attente": StatusStage.EN_ATTENTE,
#                 "en_cours": StatusStage.EN_COURS,
#                 "termine": StatusStage.TERMINE,
#                 "interrompu": StatusStage.INTERROMPU,
#                 "suspendu": StatusStage.SUSPENDU
#             }
#             if status_filter in status_mapping:
#                 query = query.filter(Stage.status == status_mapping[status_filter])
#         except Exception:
#             pass  # Ignorer les filtres invalides

#     stages = query.offset(skip).limit(limit).all()
#     return stages

@router.get("/", response_model=List[StageResponse])
def get_stages(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None
):
    query = db.query(Stage)

    # Filtrer selon le type d'utilisateur
    if current_user.type == "stagiaire":
        query = query.filter(Stage.stagiaire_id == current_user.id)
    elif current_user.type == "recruteur":
        query = query.filter(Stage.recruteur_id == current_user.id)
    elif current_user.type == "responsable_rh":
        # Les RH peuvent voir tous les stages de leur entreprise
        query = query.filter(Stage.entreprise_id == current_user.entreprise_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    # ✅ CORRECTION : Filtre par statut avec valeur string
    if status_filter:
        # Valider que le statut existe
        valid_statuses = [e.value for e in StatusStage]
        if status_filter in valid_statuses:
            # Utiliser directement la string au lieu de l'enum
            query = query.filter(Stage.status == status_filter)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Statut invalide: {status_filter}. Statuts valides: {valid_statuses}"
            )

    stages = query.offset(skip).limit(limit).all()
    return stages

@router.get("/{stage_id}", response_model=StageResponse)
def get_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer un stage spécifique."""
    
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Vérifier les permissions
    if (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
       (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce stage"
        )
    
    return stage

@router.put("/{stage_id}", response_model=StageResponse)
def update_stage(
    *,
    db: Session = Depends(get_db),
    stage_id: int,
    stage_update: StageUpdate,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """Mettre à jour un stage (recruteurs seulement)."""
    
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Vérifier que le recruteur peut modifier ce stage
    if stage.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier ce stage"
        )
    
    # Mettre à jour les champs
    update_data = stage_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stage, field, value)

    db.commit()
    db.refresh(stage)
    return stage

@router.put("/{stage_id}/action", response_model=StageResponse)
def stage_action(
    *,
    db: Session = Depends(get_db),
    stage_id: int,
    action: StageAction,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """Effectuer une action sur un stage."""

    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Vérifier les permissions
    if stage.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à gérer ce stage"
        )
    
    # Effectuer l'action
    if action.action == "commencer":
        stage.commencer_stage()
    elif action.action == "terminer":
        stage.terminer_stage(action.note_finale, action.commentaires)
    elif action.action == "interrompre":
        stage.interrompre_stage(action.commentaires)
    elif action.action == "suspendre":
        stage.suspendre_stage(action.commentaires)

    db.commit()
    db.refresh(stage)
    return stage

@router.get("/{stage_id}/candidature")
def get_stage_candidature(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer les informations de la candidature liée au stage."""

    stage = db.query(Stage).options(
        joinedload(Stage.candidature).joinedload(Candidature.offre)
    ).filter(Stage.id == stage_id).first()

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Vérifier les permissions
    if (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    return {
        "candidature_id": stage.candidature.id,
        "offre": {
            "id": stage.candidature.offre.id,
            "titre": stage.candidature.offre.titre,
            "description": stage.candidature.offre.description,
            "secteur": stage.candidature.offre.secteur
        } if stage.candidature.offre else None
    }

@router.delete("/{stage_id}")
def delete_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """Supprimer un stage (cas exceptionnel - admin seulement)."""
    stage = db.query(Stage).filter(Stage.id == stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Seuls les recruteurs de l'entreprise peuvent supprimer
    if stage.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer ce stage"
        )
    
    # Vérifier que le stage peut être supprimé (pas encore commencé)
    if stage.status != StatusStage.EN_ATTENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un stage déjà commencé"
        )
    
    db.delete(stage)
    db.commit()
    return {"message": "Stage supprimé avec succès"}