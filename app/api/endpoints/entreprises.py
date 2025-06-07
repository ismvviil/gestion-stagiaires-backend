from fastapi import APIRouter, Depends, HTTPException , Query
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
from app.api.deps import get_db
from app.models.entreprise import Entreprise
from app.schemas.entreprise import (
    Entreprise as EntrepriseSchema, 
    EntrepriseCreate, 
    EntrepriseSearch
)

router = APIRouter()

@router.get("/", response_model=List[EntrepriseSchema])
def read_entreprises(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Récupérer toutes les entreprises."""
    entreprises = db.query(Entreprise).offset(skip).limit(limit).all()
    return entreprises


@router.get("/search", response_model=List[EntrepriseSchema])
def search_entreprises(
    q: str = Query(..., min_length=2, description="Terme de recherche (minimum 2 caractères)"),
    db: Session = Depends(get_db),
    limit: int = Query(10, le=50, description="Nombre maximum de résultats")
):
    """Rechercher des entreprises par nom."""
    print(f"🔍 Recherche d'entreprises: '{q}'")
    
    # Recherche insensible à la casse avec LIKE
    entreprises = db.query(Entreprise).filter(
        func.lower(Entreprise.raison_social).contains(func.lower(q))
    ).limit(limit).all()
    
    print(f"✅ {len(entreprises)} entreprise(s) trouvée(s)")
    return entreprises

@router.get("/check-exists")
def check_entreprise_exists(
    raison_social: str = Query(..., description="Raison sociale à vérifier"),
    db: Session = Depends(get_db)
):
    """Vérifier si une entreprise existe déjà avec ce nom exact."""
    print(f"🔍 Vérification existence: '{raison_social}'")
    
    # Recherche exacte (insensible à la casse)
    entreprise = db.query(Entreprise).filter(
        func.lower(Entreprise.raison_social) == func.lower(raison_social.strip())
    ).first()
    
    exists = entreprise is not None
    print(f"{'✅' if exists else '❌'} Entreprise existe: {exists}")
    
    return {
        "exists": exists,
        "entreprise": EntrepriseSchema.model_validate(entreprise) if entreprise else None
    }


# @router.post("/", response_model=EntrepriseSchema)
# def create_entreprise(
#     entreprise_in: EntrepriseCreate,
#     db: Session = Depends(get_db),
# ):
#     """Créer une nouvelle entreprise."""
#     entreprise = Entreprise(
#         raison_social=entreprise_in.raison_social,
#         secteur_activite=entreprise_in.secteur_activite,
#         description=entreprise_in.description,
#     )
#     db.add(entreprise)
#     db.commit()
#     db.refresh(entreprise)
#     return entreprise


@router.post("/", response_model=EntrepriseSchema)
def create_entreprise(
    entreprise_in: EntrepriseCreate,
    db: Session = Depends(get_db),
):
    """Créer une nouvelle entreprise."""
    print(f"🏢 Création entreprise: {entreprise_in.raison_social}")
    
    # Vérifier que l'entreprise n'existe pas déjà
    existing = db.query(Entreprise).filter(
        func.lower(Entreprise.raison_social) == func.lower(entreprise_in.raison_social.strip())
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Une entreprise avec la raison sociale '{entreprise_in.raison_social}' existe déjà."
        )
    
    # Créer l'entreprise
    entreprise = Entreprise(
        raison_social=entreprise_in.raison_social.strip(),
        secteur_activite=entreprise_in.secteur_activite,
        description=entreprise_in.description,
        adresse=entreprise_in.adresse,
        ville=entreprise_in.ville,
        code_postal=entreprise_in.code_postal,
        pays=entreprise_in.pays,
        telephone=entreprise_in.telephone,
        site_web=entreprise_in.site_web,
        taille_entreprise=entreprise_in.taille_entreprise
    )
    
    db.add(entreprise)
    db.commit()
    db.refresh(entreprise)
    
    print(f"✅ Entreprise créée: ID {entreprise.id}")
    return entreprise

@router.get("/{entreprise_id}", response_model=EntrepriseSchema)
def get_entreprise(
    entreprise_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer une entreprise par son ID."""
    entreprise = db.query(Entreprise).filter(Entreprise.id == entreprise_id).first()
    
    if not entreprise:
        raise HTTPException(
            status_code=404,
            detail="Entreprise non trouvée"
        )
    
    return entreprise