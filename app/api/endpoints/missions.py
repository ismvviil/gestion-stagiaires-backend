from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.mission import Mission
from app.models.stage import Stage
from app.models.utilisateur import Utilisateur
from app.schemas.mission import (
    MissionCreate, MissionResponse, MissionUpdate, MissionAction , StatusMissionEnum , PrioriteMissionEnum
)

router = APIRouter()

@router.post("/", response_model=MissionResponse)
def create_mission(
    *,
    db: Session = Depends(get_db),
    mission_in: MissionCreate,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """Créer une nouvelle mission (recruteurs seulement)."""

    # Vérifier que le stage existe
    stage = db.query(Stage).filter(Stage.id == mission_in.stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Vérifier que le recruteur peut assigner des missions à ce stage
    if stage.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à assigner des missions à ce stage"
        )
    
    # Créer la mission
    # mission = Mission(
    #     **mission_in.dict(),
    #     assigne_par_id=current_user.id
    # )
    # Créer la mission AVEC des valeurs forcées
    print("=== DEBUG MISSION ===")
    print(f"mission_in.dict(): {mission_in.dict()}")

    # mission_data = mission_in.dict()
    # mission = Mission(
    #     **mission_data,
    #     assigne_par_id=current_user.id,
    #     status='a_faire',  # FORCÉ
    #     pourcentage_completion=0  # FORCÉ
    # )
    # Créer la mission manuellement
    mission = Mission()
    mission.titre = mission_in.titre
    mission.description = mission_in.description
    mission.objectifs = mission_in.objectifs
    mission.date_debut_prevue = mission_in.date_debut_prevue
    mission.date_fin_prevue = mission_in.date_fin_prevue
    mission.priorite = mission_in.priorite  # Cette ligne peut être le problème
    mission.ressources_necessaires = mission_in.ressources_necessaires
    mission.livrables_attendus = mission_in.livrables_attendus
    mission.stage_id = mission_in.stage_id
    mission.assigne_par_id = current_user.id
    
    # FORCER les valeurs par défaut
    mission.status = 'a_faire'
    mission.pourcentage_completion = 0
    
    print(f"mission.status avant save: {mission.status}")
    print(f"mission.priorite avant save: {mission.priorite}")
    
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission

@router.get("/", response_model=List[MissionResponse])
def get_missions(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
    stage_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Récupérer les missions selon le type d'utilisateur."""


    query = db.query(Mission).join(Stage)
    
    # Filtrer selon le type d'utilisateur
    if current_user.type == "stagiaire":
        query = query.filter(Stage.stagiaire_id == current_user.id)
    elif current_user.type == "recruteur":
        query = query.filter(Stage.recruteur_id == current_user.id)
    elif current_user.type == "responsable_rh":
        query = query.filter(Stage.entreprise_id == current_user.entreprise_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
     # Filtrer par stage si spécifié
    if stage_id:
        query = query.filter(Mission.stage_id == stage_id)

    # Filtrer par statut si spécifié
    if status_filter:
        try:
            status_mapping = {
                "a_faire": StatusMissionEnum.A_FAIRE,
                "en_cours": StatusMissionEnum.EN_COURS,
                "en_revision": StatusMissionEnum.EN_REVISION,
                "terminee": StatusMissionEnum.TERMINEE,
                "annulee": StatusMissionEnum.ANNULEE
            }
            if status_filter in status_mapping:
                query = query.filter(Mission.status == status_mapping[status_filter])
        except Exception:
            pass
    
    missions = query.offset(skip).limit(limit).all()
    return missions

@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer une mission spécifique."""
    
    mission = db.query(Mission).options(
        joinedload(Mission.stage)
    ).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée"
        )
    
    # Vérifier les permissions
    stage = mission.stage
    if (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
       (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à cette mission"
        )
    
    return mission

@router.put("/{mission_id}", response_model=MissionResponse)
def update_mission(
    *,
    db: Session = Depends(get_db),
    mission_id: int,
    mission_update: MissionUpdate,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Mettre à jour une mission."""
    
    mission = db.query(Mission).options(
        joinedload(Mission.stage)
    ).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée"
        )
    
    stage = mission.stage

    # Permissions selon le type d'utilisateur
    if current_user.type == "recruteur":
        # Recruteur peut tout modifier
        if stage.recruteur_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier cette mission"
            )
        
    elif current_user.type == "stagiaire":
        # Stagiaire peut seulement modifier certains champs
        if stage.stagiaire_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à modifier cette mission"
            )
        # Limiter les champs modifiables par le stagiaire
        allowed_fields = ["pourcentage_completion", "feedback_stagiaire", "livrables_fournis", "outils_utilises"]
        update_data = {k: v for k, v in mission_update.dict(exclude_unset=True).items() if k in allowed_fields}

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )

    # Mettre à jour
    if current_user.type == "recruteur":
        update_data = mission_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(mission, field, value)

    db.commit()
    db.refresh(mission)
    return mission


@router.put("/{mission_id}/action", response_model=MissionResponse)
def mission_action(
    *,
    db: Session = Depends(get_db),
    mission_id: int,
    action: MissionAction,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Effectuer une action sur une mission."""

    mission = db.query(Mission).options(
        joinedload(Mission.stage)
    ).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée"
        )
    
    stage = mission.stage

     # Vérifier les permissions selon l'action
    if action.action in ["commencer", "soumettre"]:
        # Actions que le stagiaire peut faire
        if current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à effectuer cette action"
            )
    elif action.action in ["valider", "rejeter", "annuler"]:
        # Actions que seul le recruteur peut faire
        if current_user.type != "recruteur" or stage.recruteur_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul le recruteur peut effectuer cette action"
            )
        
    # Effectuer l'action
    if action.action == "commencer":
        mission.commencer_mission()
    elif action.action == "soumettre":
        mission.soumettre_mission(action.livrables, action.feedback)
    elif action.action == "valider":
        mission.valider_mission(action.note, action.feedback)

    elif action.action == "rejeter":
        if not action.feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un feedback est requis pour rejeter une mission"
            )
        mission.rejeter_mission(action.feedback)

    elif action.action == "annuler":
        if not action.feedback:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une raison est requise pour annuler une mission"
            )
        mission.annuler_mission(action.feedback)

    # Mettre à jour la progression si fournie
    if action.pourcentage is not None:
        mission.mettre_a_jour_progression(action.pourcentage)
    
    db.commit()
    db.refresh(mission)
    return mission

@router.delete("/{mission_id}")
def delete_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """Supprimer une mission (recruteurs seulement)."""

    mission = db.query(Mission).options(
        joinedload(Mission.stage)
    ).filter(Mission.id == mission_id).first()
    
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission non trouvée"
        )
    
     # Vérifier les permissions
    if mission.stage.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer cette mission"
        )
    
    # Vérifier que la mission peut être supprimée
    if mission.status in [StatusMissionEnum.EN_COURS, StatusMissionEnum.EN_REVISION]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer une mission en cours ou en révision"
        )
    
    db.delete(mission)
    db.commit()
    return {"message": "Mission supprimée avec succès"}

@router.get("/stage/{stage_id}/missions", response_model=List[MissionResponse])
def get_missions_by_stage(
    stage_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer toutes les missions d'un stage."""

    """Récupérer toutes les missions d'un stage."""
    
    # Vérifier que le stage existe et les permissions
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
            detail="Accès non autorisé"
        )
    
    missions = db.query(Mission).filter(Mission.stage_id == stage_id).all()
    return missions
