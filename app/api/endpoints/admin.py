from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.utilisateur import Utilisateur
from app.schemas.admin_stats import (
    StatistiquesGlobales, StatistiquesTemporelles, StatistiquesEntreprises,
    StatistiquesSecteurs, UtilisateurDetaille
)
from app.services.admin_stats_service import AdminStatsService

router = APIRouter()

@router.get("/stats/globales", response_model=StatistiquesGlobales)
def get_statistiques_globales(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("admin"))
):
    """Obtenir les statistiques globales de la plateforme."""
    return AdminStatsService.obtenir_statistiques_globales(db)

@router.get("/stats/evolution", response_model=List[StatistiquesTemporelles])
def get_evolution_temporelle(
    mois: int = Query(12, ge=1, le=24, description="Nombre de mois à récupérer"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("admin"))
):
    """Obtenir l'évolution temporelle des métriques."""
    return AdminStatsService.obtenir_evolution_temporelle(db, mois)

@router.get("/stats/entreprises", response_model=List[StatistiquesEntreprises])
def get_stats_entreprises(
    limit: int = Query(20, ge=5, le=100, description="Nombre d'entreprises à retourner"),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("admin"))
):
    """Obtenir les statistiques des principales entreprises."""
    return AdminStatsService.obtenir_stats_entreprises(db, limit)


@router.get("/stats/secteurs", response_model=List[StatistiquesSecteurs])
def get_stats_secteurs(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("admin"))
):
    """Obtenir les statistiques par secteur d'activité."""
    return AdminStatsService.obtenir_stats_secteurs(db)

@router.get("/utilisateurs", response_model=List[UtilisateurDetaille])
def get_utilisateurs_details(
    type_filtre: Optional[str] = Query(None, description="Filtrer par type d'utilisateur"),
    actif_filtre: Optional[bool] = Query(None, description="Filtrer par statut actif"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("admin"))
):
    """Obtenir la liste détaillée des utilisateurs."""
    return AdminStatsService.obtenir_utilisateurs_details(
        db, type_filtre, actif_filtre, skip, limit
    )

@router.patch("/utilisateurs/{user_id}/toggle-status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("admin"))
):
    """Activer/désactiver un utilisateur."""
    
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Empêcher la désactivation d'autres admins
    if user.type == "admin" and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de modifier le statut d'un autre admin"
        )
    
    user.actif = not user.actif
    db.commit()
    
    return {
        "message": f"Utilisateur {'activé' if user.actif else 'désactivé'} avec succès",
        "user_id": user.id,
        "nouveau_statut": user.actif
    }
