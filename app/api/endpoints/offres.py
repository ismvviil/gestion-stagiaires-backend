from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.offre import Offre
from app.models.utilisateur import Utilisateur
from app.models.recruteur import Recruteur
from app.models.candidature import Candidature
from app.schemas.offre import OffreCreate, OffreUpdate, Offre as OffreSchema, OffreSearchResult

router = APIRouter()

@router.post("/", response_model=OffreSchema)
def create_offre(
    *,
    db: Session = Depends(get_db),
    offre_in: OffreCreate,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """
    Créer une nouvelle offre de stage.
    Seuls les recruteurs peuvent créer des offres.
    """
    # Vérifier que l'entreprise du recruteur correspond à l'entreprise de l'offre
    if current_user.entreprise_id != offre_in.entreprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez créer des offres que pour votre entreprise"
        )
    
    offre = Offre(
        **offre_in.dict(),
        recruteur_id=current_user.id
    )
    db.add(offre)
    db.commit()
    db.refresh(offre)
    return offre

@router.get("/", response_model=OffreSearchResult)
def read_offres(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    titre: Optional[str] = None,
    secteur: Optional[str] = None,
    type_stage: Optional[str] = None,
    localisation: Optional[str] = None,
    entreprise_id: Optional[int] = None,
    date_debut_min: Optional[date] = None,
    date_debut_max: Optional[date] = None,
    est_active: Optional[bool] = True,
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer toutes les offres de stage avec filtrage.
    """
    query = db.query(Offre)
    
    # Appliquer les filtres si spécifiés
    if titre:
        query = query.filter(Offre.titre.ilike(f"%{titre}%"))
    if secteur:
        query = query.filter(Offre.secteur == secteur)
    if type_stage:
        query = query.filter(Offre.type_stage == type_stage)
    if localisation:
        query = query.filter(Offre.localisation.ilike(f"%{localisation}%"))
    if entreprise_id:
        query = query.filter(Offre.entreprise_id == entreprise_id)
    if date_debut_min:
        query = query.filter(Offre.date_debut >= date_debut_min)
    if date_debut_max:
        query = query.filter(Offre.date_debut <= date_debut_max)
    if est_active is not None:
        query = query.filter(Offre.est_active == est_active)
    
    # Si l'utilisateur est un recruteur, ne montrer que ses offres et celles de son entreprise
    if current_user.type == "recruteur":
        recruteur = db.query(Recruteur).filter(Recruteur.id == current_user.id).first()
        query = query.filter(Offre.entreprise_id == recruteur.entreprise_id)
    
    total = query.count()
    offres = query.offset(skip).limit(limit).all()
    
    return {"total": total, "offres": offres}

@router.get("/{offre_id}", response_model=OffreSchema)
def read_offre(
    *,
    db: Session = Depends(get_db),
    offre_id: int,
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Récupérer une offre de stage par son ID.
    """
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offre non trouvée"
        )
    
    return offre


@router.put("/{offre_id}", response_model=OffreSchema)
def update_offre(
    *,
    db: Session = Depends(get_db),
    offre_id: int,
    offre_in: OffreUpdate,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """
    Mettre à jour une offre de stage.
    Seul le recruteur qui a créé l'offre peut la modifier.
    """
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offre non trouvée"
        )
    
    if offre.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette offre"
        )
    
    update_data = offre_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(offre, field, value)
    
    db.add(offre)
    db.commit()
    db.refresh(offre)
    return offre

# @router.delete("/{offre_id}", response_model=OffreSchema)
# def delete_offre(
#     *,
#     db: Session = Depends(get_db),
#     offre_id: int,
#     current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
# ):
#     """
#     Supprimer une offre de stage.
#     Seul le recruteur qui a créé l'offre peut la supprimer.
#     """
#     offre = db.query(Offre).filter(Offre.id == offre_id).first()
#     if not offre:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Offre non trouvée"
#         )
    
#     if offre.recruteur_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Vous n'êtes pas autorisé à supprimer cette offre"
#         )
    
#     db.delete(offre)
#     db.commit()
#     return offre
# @router.delete("/{offre_id}", response_model=OffreSchema)
# def delete_offre(
#     *,
#     db: Session = Depends(get_db),
#     offre_id: int,
#     current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
# ):
#     offre = db.query(Offre).filter(Offre.id == offre_id).first()
#     if not offre:
#         raise HTTPException(status_code=404, detail="Offre non trouvée")
    
#     if offre.recruteur_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à supprimer cette offre")
    
#     # Charger entreprise pour éviter l'erreur de session détachée
#     _ = offre.entreprise  # force SQLAlchemy à charger entreprise avant suppression
    
#     # Créer une copie Pydantic de l'objet avant suppression
#     response_data = OffreSchema.from_orm(offre)

#     db.delete(offre)
#     db.commit()
#     return response_data
@router.delete("/{offre_id}", response_model=OffreSchema)
def delete_offre(
    *,
    db: Session = Depends(get_db),
    offre_id: int,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")

    if offre.recruteur_id != current_user.id:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à supprimer cette offre")

    # Vérifie s'il y a des candidatures liées à cette offre
    candidatures = db.query(Candidature).filter(Candidature.offre_id == offre.id).count()

    if candidatures > 0:
        # Soft delete
        offre.est_active = False
        db.commit()
        return OffreSchema.from_orm(offre)
    else:
        # Suppression physique
        _ = offre.entreprise  # charger entreprise pour éviter DetachedInstanceError
        response_data = OffreSchema.from_orm(offre)
        db.delete(offre)
        db.commit()
        return response_data


@router.put("/{offre_id}/publier", response_model=OffreSchema)
def publier_offre(
    *,
    db: Session = Depends(get_db),
    offre_id: int,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """
    Publier une offre de stage (la rendre active).
    Seul le recruteur qui a créé l'offre peut la publier.
    """
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offre non trouvée"
        )
    
    if offre.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à publier cette offre"
        )
    
    offre.est_active = True
    db.add(offre)
    db.commit()
    db.refresh(offre)
    return offre

@router.put("/{offre_id}/fermer", response_model=OffreSchema)
def fermer_offre(
    *,
    db: Session = Depends(get_db),
    offre_id: int,
    current_user: Utilisateur = Depends(get_user_by_type("recruteur"))
):
    """
    Fermer une offre de stage (la rendre inactive).
    Seul le recruteur qui a créé l'offre peut la fermer.
    """
    offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if not offre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offre non trouvée"
        )
    
    if offre.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à fermer cette offre"
        )
    
    offre.est_active = False
    db.add(offre)
    db.commit()
    db.refresh(offre)
    return offre