# app/api/endpoints/evaluations.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import tempfile
import os
from fastapi.responses import FileResponse, StreamingResponse
from io import BytesIO
from sqlalchemy.sql import func , or_ # 🆕 AJOUT pour func.now()

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.utilisateur import Utilisateur
from app.models.evaluation import Evaluation, CritereEvaluation, Certificat , DetailEvaluation
from app.models.stage import Stage
from app.schemas.evaluation import (
    EvaluationCreate, EvaluationUpdate, Evaluation as EvaluationSchema,
    EvaluationValidation, CritereEvaluation as CritereEvaluationSchema,
    Certificat as CertificatSchema,  # 🆕 AJOUT pour response_model
    StatistiquesEvaluation,
        CertificatPublic,
          EvaluationWithRelations  # 🆕 AJOUT pour vérification publique

)
from app.services.evaluation_service import EvaluationService
from app.models.candidature import Candidature
from app.models.stagiaire import Stagiaire

# Schémas Pydantic
router = APIRouter()

# ============================================================================
# CRITÈRES D'ÉVALUATION
# ============================================================================

@router.get("/criteres", response_model=List[CritereEvaluationSchema])
def get_criteres_evaluation(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer les critères d'évaluation disponibles."""
    entreprise_id = None
    if hasattr(current_user, 'entreprise_id'):
        entreprise_id = current_user.entreprise_id
    
    criteres = EvaluationService.obtenir_criteres_evaluation(db, entreprise_id)
    return criteres

# ============================================================================
# ÉVALUATIONS
# ============================================================================

@router.post("/", response_model=EvaluationSchema)
def create_evaluation(
    *,
    db: Session = Depends(get_db),
    evaluation_in: EvaluationCreate,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Créer une nouvelle évaluation (RH ou Recruteur)."""
    
    # Vérifier les permissions
    if current_user.type not in ["responsable_rh", "recruteur"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les RH et recruteurs peuvent créer des évaluations"
        )
    
    # Vérifier que l'utilisateur peut évaluer ce stage
    stage = db.query(Stage).filter(Stage.id == evaluation_in.stage_id).first()
    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stage non trouvé"
        )
    
    # Permissions selon le type d'utilisateur
    if current_user.type == "recruteur" and stage.recruteur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez évaluer que vos propres stages"
        )
    elif current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez évaluer que les stages de votre entreprise"
        )
    
    try:
        evaluation = EvaluationService.creer_evaluation(
            db, evaluation_in, current_user.id
        )
        return evaluation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get("/")
def get_evaluations(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    statut: Optional[str] = None,
    search: Optional[str] = None  # 🔧 AJOUTER LE PARAMÈTRE SEARCH

):
    """Récupérer les évaluations selon le type d'utilisateur."""
    
    # query = db.query(Evaluation).join(Stage)

    # 🔥 QUERY AVEC JOINEDLOAD EXPLICITES
    query = db.query(Evaluation).options(
        # Charger l'évaluateur
        joinedload(Evaluation.evaluateur),
        # Charger le stage avec ses relations
        joinedload(Evaluation.stage).joinedload(Stage.stagiaire),
        joinedload(Evaluation.stage).joinedload(Stage.entreprise),
        joinedload(Evaluation.stage).joinedload(Stage.candidature).joinedload(Candidature.offre),
        # Charger les détails avec critères
        joinedload(Evaluation.details).joinedload(DetailEvaluation.critere)
    )

    # Joindre Stage pour les filtres
    query = query.join(Stage)

    # Filtrer selon le type d'utilisateur
    if current_user.type == "responsable_rh":
        query = query.filter(Stage.entreprise_id == current_user.entreprise_id)
    elif current_user.type == "recruteur":
        query = query.filter(Stage.recruteur_id == current_user.id)
    elif current_user.type == "stagiaire":
        query = query.filter(Stage.stagiaire_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    # Filtre par statut si spécifié
    if statut:
        from app.models.evaluation import StatutEvaluation
        try:
            statut_enum = StatutEvaluation(statut)
            query = query.filter(Evaluation.statut == statut_enum)
        except ValueError:
            pass  # Ignorer les statuts invalides
    
    # 🔧 FILTRE PAR RECHERCHE (nom/prénom du stagiaire) - CORRECTION
    if search:
        search_term = f"%{search.lower()}%"
        # Joindre avec la table Stagiaire pour la recherche
        query = query.join(Stage.stagiaire)
        query = query.filter(
            or_(  # 🔧 CORRECTION : or_ au lieu de db.or_
                func.lower(Stagiaire.nom).like(search_term),
                func.lower(Stagiaire.prenom).like(search_term),
                func.lower(func.concat(Stagiaire.prenom, ' ', Stagiaire.nom)).like(search_term),
                func.lower(func.concat(Stagiaire.nom, ' ', Stagiaire.prenom)).like(search_term)
            )
        )
    # evaluations = query.offset(skip).limit(limit).all()
    # return evaluations
    # 🔥 AJOUTER L'ORDRE POUR AVOIR LES PLUS RÉCENTES EN PREMIER
    evaluations = query.order_by(Evaluation.date_evaluation.desc()).offset(skip).limit(limit).all()

    # 🔥 DEBUG CÔTÉ SERVEUR
    print(f"📊 Nombre d'évaluations trouvées: {len(evaluations)}")
    if evaluations:
        eval_test = evaluations[0]
        print(f"📊 Première évaluation - ID: {eval_test.id}")
        print(f"📊 Stage chargé: {eval_test.stage is not None}")
        print(f"📊 Evaluateur chargé: {eval_test.evaluateur is not None}")
        if eval_test.stage:
            print(f"📊 Stagiaire chargé: {eval_test.stage.stagiaire is not None}")
            print(f"📊 Candidature chargée: {eval_test.stage.candidature is not None}")
            
     # 🔥 CONSTRUCTION MANUELLE GARANTIE DE FONCTIONNER
    result = []
    for eval in evaluations:
        eval_dict = {
            "id": eval.id,
            "statut": eval.statut.value,
            "note_globale": eval.note_globale,
            "date_evaluation": eval.date_evaluation.isoformat(),
            "date_validation": eval.date_validation.isoformat() if eval.date_validation else None,
            "commentaire_general": eval.commentaire_general,
            "points_forts": eval.points_forts,
            "points_amelioration": eval.points_amelioration,
            "recommandations": eval.recommandations,
            "recommande_embauche": eval.recommande_embauche,
            "stage_id": eval.stage_id,
            "evaluateur_id": eval.evaluateur_id,
            "created_at": eval.created_at.isoformat() if eval.created_at else None,
            "updated_at": eval.updated_at.isoformat() if eval.updated_at else None,
        }
        
        # 🔥 AJOUTER LES RELATIONS SI ELLES EXISTENT
        if eval.stage:
            eval_dict["stage"] = {
                "id": eval.stage.id,
                "description": eval.stage.description,
                "date_debut": eval.stage.date_debut.isoformat(),
                "date_fin": eval.stage.date_fin.isoformat(),
            }
            
            # Stagiaire
            if eval.stage.stagiaire:
                eval_dict["stage"]["stagiaire"] = {
                    "id": eval.stage.stagiaire.id,
                    "nom": eval.stage.stagiaire.nom,
                    "prenom": eval.stage.stagiaire.prenom
                }
            
            # Candidature et offre
            if eval.stage.candidature:
                eval_dict["stage"]["candidature"] = {
                    "id": eval.stage.candidature.id
                }
                if eval.stage.candidature.offre:
                    eval_dict["stage"]["candidature"]["offre"] = {
                        "id": eval.stage.candidature.offre.id,
                        "titre": eval.stage.candidature.offre.titre
                    }
        
        # Evaluateur
        if eval.evaluateur:
            eval_dict["evaluateur"] = {
                "id": eval.evaluateur.id,
                "nom": eval.evaluateur.nom,
                "prenom": eval.evaluateur.prenom,
                "type": eval.evaluateur.type
            }
        
        result.append(eval_dict)
    
    print(f"📊 Retour de {len(result)} évaluations avec relations")
    if result:
        print(f"📊 Première évaluation stage: {result[0].get('stage', {}).get('stagiaire', 'Non trouvé')}")
    
    return result
    # return evaluations

# @router.get("/{evaluation_id}", response_model=EvaluationSchema)
# def get_evaluation(
#     evaluation_id: int,
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_current_user)
# ):
#     """Récupérer une évaluation spécifique."""

#     evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
#     if not evaluation:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Évaluation non trouvée"
#         )
    
#     # Vérifier les permissions
#     stage = evaluation.stage
#     if (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id) or \
#        (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
#        (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Accès non autorisé à cette évaluation"
#         )
    
#     return evaluation
@router.get("/{evaluation_id}")
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer une évaluation spécifique avec toutes les relations."""
    
    # 🔧 Charger l'évaluation avec toutes les relations nécessaires
    evaluation = db.query(Evaluation)\
        .options(
            # Charger l'évaluateur
            joinedload(Evaluation.evaluateur),
            # Charger le stage avec ses relations
            joinedload(Evaluation.stage).joinedload(Stage.stagiaire),
            joinedload(Evaluation.stage).joinedload(Stage.entreprise),
            joinedload(Evaluation.stage).joinedload(Stage.candidature).joinedload(Candidature.offre),
            # Charger les détails avec critères
            joinedload(Evaluation.details).joinedload(DetailEvaluation.critere)
        )\
        .filter(Evaluation.id == evaluation_id)\
        .first()
    
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation non trouvée"
        )
    
    # Vérifier les permissions
    stage = evaluation.stage
    if (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
       (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à cette évaluation"
        )
    
    # 🔧 Debug pour voir les relations chargées
    print(f"📊 Évaluation {evaluation.id} - Relations chargées:")
    print(f"  - Stage: {evaluation.stage is not None}")
    if evaluation.stage:
        print(f"  - Stagiaire: {evaluation.stage.stagiaire is not None}")
        print(f"  - Entreprise: {evaluation.stage.entreprise is not None}")
        print(f"  - Candidature: {evaluation.stage.candidature is not None}")
        if evaluation.stage.candidature:
            print(f"  - Offre: {evaluation.stage.candidature.offre is not None}")
    print(f"  - Evaluateur: {evaluation.evaluateur is not None}")
    print(f"  - Détails: {len(evaluation.details) if evaluation.details else 0}")
    
    # 🔧 Construire la réponse manuelle comme pour la liste
    eval_dict = {
        "id": evaluation.id,
        "statut": evaluation.statut.value,
        "note_globale": evaluation.note_globale,
        "date_evaluation": evaluation.date_evaluation.isoformat(),
        "date_validation": evaluation.date_validation.isoformat() if evaluation.date_validation else None,
        "commentaire_general": evaluation.commentaire_general,
        "points_forts": evaluation.points_forts,
        "points_amelioration": evaluation.points_amelioration,
        "recommandations": evaluation.recommandations,
        "recommande_embauche": evaluation.recommande_embauche,
        "stage_id": evaluation.stage_id,
        "evaluateur_id": evaluation.evaluateur_id,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
        "updated_at": evaluation.updated_at.isoformat() if evaluation.updated_at else None,
    }
    
    # 🔧 Ajouter les relations Stage
    if evaluation.stage:
        eval_dict["stage"] = {
            "id": evaluation.stage.id,
            "description": evaluation.stage.description,
            "date_debut": evaluation.stage.date_debut.isoformat(),
            "date_fin": evaluation.stage.date_fin.isoformat(),
            "status": evaluation.stage.status,
            "objectifs": evaluation.stage.objectifs,
            # 🎯 Titre calculé pour le frontend
            "titre": None  # On va le calculer après
        }
        
        # Stagiaire
        if evaluation.stage.stagiaire:
            eval_dict["stage"]["stagiaire"] = {
                "id": evaluation.stage.stagiaire.id,
                "nom": evaluation.stage.stagiaire.nom,
                "prenom": evaluation.stage.stagiaire.prenom,
                "email": evaluation.stage.stagiaire.email
            }
        
        # Entreprise
        if evaluation.stage.entreprise:
            eval_dict["stage"]["entreprise"] = {
                "id": evaluation.stage.entreprise.id,
                "raison_social": evaluation.stage.entreprise.raison_social,
                "nom": evaluation.stage.entreprise.raison_social  # Alias pour compatibilité
            }
        
        # Candidature et offre
        if evaluation.stage.candidature:
            eval_dict["stage"]["candidature"] = {
                "id": evaluation.stage.candidature.id
            }
            if evaluation.stage.candidature.offre:
                eval_dict["stage"]["candidature"]["offre"] = {
                    "id": evaluation.stage.candidature.offre.id,
                    "titre": evaluation.stage.candidature.offre.titre,
                    "description": evaluation.stage.candidature.offre.description
                }
                # 🎯 Utiliser le titre de l'offre comme titre du stage
                eval_dict["stage"]["titre"] = evaluation.stage.candidature.offre.titre
            
        # 🎯 Si pas de titre d'offre, utiliser la description du stage
        if not eval_dict["stage"]["titre"]:
            eval_dict["stage"]["titre"] = evaluation.stage.description or "Stage"
    
    # 🔧 Ajouter l'évaluateur
    if evaluation.evaluateur:
        eval_dict["evaluateur"] = {
            "id": evaluation.evaluateur.id,
            "nom": evaluation.evaluateur.nom,
            "prenom": evaluation.evaluateur.prenom,
            "email": evaluation.evaluateur.email,
            "type": evaluation.evaluateur.type
        }
    
    # 🔧 Ajouter les détails d'évaluation
    if evaluation.details:
        eval_dict["details"] = []
        for detail in evaluation.details:
            detail_dict = {
                "id": detail.id,
                "note": detail.note,
                "commentaire": detail.commentaire,
                "evaluation_id": detail.evaluation_id,
                "critere_id": detail.critere_id
            }
            
            # Ajouter le critère
            if detail.critere:
                detail_dict["critere"] = {
                    "id": detail.critere.id,
                    "nom": detail.critere.nom,
                    "description": detail.critere.description,
                    "type_critere": detail.critere.type_critere.value if detail.critere.type_critere else None,
                    "poids": detail.critere.poids,
                    "actif": detail.critere.actif
                }
            
            eval_dict["details"].append(detail_dict)
    
    print(f"📊 Retour évaluation {evaluation.id} avec toutes les relations")
    if eval_dict.get("stage", {}).get("stagiaire"):
        print(f"📊 Stagiaire: {eval_dict['stage']['stagiaire']['prenom']} {eval_dict['stage']['stagiaire']['nom']}")
    if eval_dict.get("stage", {}).get("titre"):
        print(f"📊 Titre: {eval_dict['stage']['titre']}")
    if eval_dict.get("evaluateur"):
        print(f"📊 Évaluateur: {eval_dict['evaluateur']['prenom']} {eval_dict['evaluateur']['nom']}")
    
    return eval_dict

@router.put("/{evaluation_id}", response_model=EvaluationSchema)
def update_evaluation(
    *,
    db: Session = Depends(get_db),
    evaluation_id: int,
    evaluation_update: EvaluationUpdate,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Mettre à jour une évaluation (si pas encore validée)."""

    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation non trouvée"
        )
    
    # Vérifier que c'est l'évaluateur
    if evaluation.evaluateur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez modifier que vos propres évaluations"
        )
    
    # Vérifier que l'évaluation n'est pas validée
    from app.models.evaluation import StatutEvaluation
    if evaluation.statut == StatutEvaluation.VALIDEE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier une évaluation validée"
        )
    
    # Mettre à jour les champs
    update_data = evaluation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "details":  # Gérer les détails séparément
            setattr(evaluation, field, value)

    # Recalculer la note globale si nécessaire
    if hasattr(evaluation_update, 'details') and evaluation_update.details:
        # Supprimer les anciens détails
        from app.models.evaluation import DetailEvaluation
        db.query(DetailEvaluation).filter(
            DetailEvaluation.evaluation_id == evaluation.id
        ).delete()
        
        # Ajouter les nouveaux détails
        for detail_data in evaluation_update.details:
            detail = DetailEvaluation(
                **detail_data.dict(),
                evaluation_id=evaluation.id
            )
            db.add(detail)
        
        evaluation.calculer_note_globale()

    db.commit()
    db.refresh(evaluation)
    return evaluation



# ""jdgggbhnddddddddddddddddddddddddddddddddddddd#################################

@router.post("/{evaluation_id}/terminer", response_model=EvaluationSchema)
def terminer_evaluation(
    *,
    db: Session = Depends(get_db),
    evaluation_id: int,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Terminer une évaluation (marquer comme terminée)."""
    
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation non trouvée"
        )
    
    # Vérifier que c'est l'évaluateur
    if evaluation.evaluateur_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez terminer que vos propres évaluations"
        )
    
    # Vérifier que l'évaluation est en brouillon
    from app.models.evaluation import StatutEvaluation
    if evaluation.statut != StatutEvaluation.BROUILLON:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les évaluations en brouillon peuvent être terminées"
        )
    
    # Vérifier qu'il y a des détails
    if not evaluation.details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'évaluation doit contenir au moins un critère évalué"
        )
    
    # Terminer l'évaluation
    evaluation.statut = StatutEvaluation.TERMINEE
    db.commit()
    db.refresh(evaluation)
    return evaluation


# ""jdgggbhnddddddddddddddddddddddddddddddddddddd#################################

@router.post("/{evaluation_id}/valider", response_model=EvaluationSchema)
def valider_evaluation(
    *,
    db: Session = Depends(get_db),
    evaluation_id: int,
    validation: EvaluationValidation,
    current_user: Utilisateur = Depends(get_current_user)
):
    """Valider une évaluation (RH seulement)."""
    
    if current_user.type != "responsable_rh":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les responsables RH peuvent valider les évaluations"
        )
    
    try:
        evaluation = EvaluationService.valider_evaluation(db, evaluation_id)
        return evaluation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
# @router.get("/statistiques/entreprise", response_model=StatistiquesEvaluation)
# def get_statistiques_evaluations(
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_user_by_type("responsable_rh"))
# ):
#     """Obtenir les statistiques d'évaluation de l'entreprise."""
    
#     stats = EvaluationService.calculer_statistiques_evaluation(
#         db, current_user.entreprise_id
#     )
#     return stats

@router.get("/statistiques/entreprise", response_model=StatistiquesEvaluation)
def get_statistiques_evaluations(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)  # 🔧 CHANGEMENT ICI
):
    """Obtenir les statistiques d'évaluation selon le rôle utilisateur."""
    
    # 🔧 Vérifier les permissions
    if current_user.type not in ["responsable_rh", "recruteur"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé aux statistiques"
        )
    
    # 🔧 Adapter le calcul selon le rôle
    if current_user.type == "responsable_rh":
        # RH voit les statistiques de toute l'entreprise
        stats = EvaluationService.calculer_statistiques_evaluation(
            db, current_user.entreprise_id
        )
    elif current_user.type == "recruteur":
        # Recruteur voit ses propres statistiques
        stats = EvaluationService.calculer_statistiques_recruteur(
            db, current_user.id
        )
    
    return stats

# ============================================================================
# CERTIFICATS
# ============================================================================

# @router.post("/certificats/generer")
# def generer_certificat(
#     *,
#     db: Session = Depends(get_db),
#     evaluation_id: int,
#     current_user: Utilisateur = Depends(get_user_by_type("responsable_rh"))
# ):
#     """Générer un certificat à partir d'une évaluation validée."""

#     try:
#         from app.services.evaluation_service import CertificatService
#         certificat = CertificatService.generer_certificat(
#             db, evaluation_id, current_user.id
#         )
#         return {
#             "message": "Certificat généré avec succès",
#             "certificat_id": certificat.id,
#             "code_unique": certificat.code_unique
#         }
#     except ValueError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=str(e)
#         )
    
@router.post("/certificats/generer")
def generer_certificat(
    *,
    db: Session = Depends(get_db),
    evaluation_id: int,
    current_user: Utilisateur = Depends(get_current_user)  # 🔧 Changement ici
):
    """Générer un certificat à partir d'une évaluation validée."""
    
    # 🔧 Vérifier les permissions manuellement
    if current_user.type not in ["responsable_rh", "recruteur"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les RH et recruteurs peuvent générer des certificats"
        )
    
    # 🔧 Vérifier que le recruteur ne peut générer que pour ses évaluations
    if current_user.type == "recruteur":
        evaluation_check = db.query(Evaluation)\
            .join(Stage)\
            .filter(
                Evaluation.id == evaluation_id,
                Stage.recruteur_id == current_user.id
            ).first()
        
        if not evaluation_check:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez générer des certificats que pour vos propres évaluations"
            )
    
    # 🔧 RH peut générer pour toutes les évaluations de son entreprise
    elif current_user.type == "responsable_rh":
        evaluation_check = db.query(Evaluation)\
            .join(Stage)\
            .filter(
                Evaluation.id == evaluation_id,
                Stage.entreprise_id == current_user.entreprise_id
            ).first()
        
        if not evaluation_check:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez générer des certificats que pour les évaluations de votre entreprise"
            )
    
    try:
        from app.services.evaluation_service import CertificatService
        
        # 🔧 Utiliser le service corrigé qui retourne un dictionnaire
        result = CertificatService.generer_certificat(
            db, evaluation_id, current_user.id
        )
        
        # 🔧 Adapter la réponse selon le cas
        if result["deja_genere"]:
            return {
                "success": True,
                "message": result["message"],
                "certificat_id": result["certificat"].id if result["certificat"] else None,
                "code_unique": result["code_unique"],
                "deja_existant": True
            }
        else:
            return {
                "success": True,
                "message": result["message"],
                "certificat_id": result["certificat"].id,
                "code_unique": result["code_unique"],
                "deja_existant": False
            }
            
    except ValueError as e:
        print(f"🔧 ValueError dans endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"🔧 Erreur générale dans endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la génération du certificat"
        )
    

@router.get("/certificats/{certificat_id}/pdf")
def telecharger_certificat_pdf(
    certificat_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Télécharger le PDF d'un certificat."""
    
    certificat = db.query(Certificat).filter(Certificat.id == certificat_id).first()
    if not certificat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificat non trouvé"
        )

    #Vérifier les permissions
    stage = certificat.stage
    if (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
       (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce certificat"
        )
    
    # Générer le PDF à la demande
    try:
        from app.services.pdf_service import PDFService
        pdf_buffer = PDFService.generer_certificat_pdf(certificat)

         # Marquer comme téléchargé
        from app.services.evaluation_service import CertificatService
        CertificatService.marquer_comme_telecharge(db, certificat_id)

        # Retourner le PDF
        filename = f"certificat_{certificat.code_unique}.pdf"

        return StreamingResponse(
            BytesIO(pdf_buffer),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )
    
# ============================================================================
# VÉRIFICATION PUBLIQUE (SANS AUTHENTIFICATION)
# ============================================================================

@router.get("/certificats/verify/{code_unique}")
def verifier_certificat_public(code_unique: str, db: Session = Depends(get_db)):
    """Vérification publique d'un certificat via QR code (accès guest)."""

    try:
        from app.services.evaluation_service import VerificationService
        from app.schemas.evaluation import CertificatPublic
        
        resultat = VerificationService.verifier_par_qr_code(db, code_unique)
        
        if not resultat["valide"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=resultat["message"]
            )
        
        # Convertir en schéma public (sans données sensibles)
        certificat = resultat["certificat"]
        certificat_public = CertificatPublic(
            code_unique=certificat.code_unique,
            titre_stage=certificat.titre_stage,
            date_debut_stage=certificat.date_debut_stage,
            date_fin_stage=certificat.date_fin_stage,
            duree_stage_jours=certificat.duree_stage_jours,
            note_finale=certificat.note_finale,
            mention=certificat.mention,
            nom_stagiaire=certificat.nom_stagiaire,
            prenom_stagiaire=certificat.prenom_stagiaire,
            nom_entreprise=certificat.nom_entreprise,
            secteur_entreprise=certificat.secteur_entreprise,
            date_generation=certificat.date_generation,
            est_valide=True
        )

        return {
            "valide": True,
            "message": resultat["message"],
            "certificat": certificat_public,
            "verification_numero": resultat["verification_numero"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification: {str(e)}"
        )


@router.get("/certificats/{certificat_id}/qr-code")
def get_qr_code(
    certificat_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer le QR code d'un certificat."""

    certificat = db.query(Certificat).filter(Certificat.id == certificat_id).first()
    if not certificat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificat non trouvé"
        )
    
    # Vérifier les permissions (même logique que pour le PDF)
    stage = certificat.stage
    if (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
       (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce certificat"
        )
    
    return {
        "code_unique": certificat.code_unique,
        "qr_code_data": certificat.qr_code_data,
        "verification_url": f"/api/evaluations/certificats/verify/{certificat.code_unique}"
    }



# ============================================================================
# ENDPOINTS MANQUANTS POUR LES CERTIFICATS
# ============================================================================

@router.get("/certificats/", response_model=List[CertificatSchema])
def get_certificates(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    mention: Optional[str] = None,
    annee: Optional[int] = None
):
    """Récupérer la liste des certificats avec filtres."""
    
    query = db.query(Certificat).join(Stage)
    
    # Filtrer selon le type d'utilisateur
    if current_user.type == "responsable_rh":
        query = query.filter(Stage.entreprise_id == current_user.entreprise_id)
    elif current_user.type == "recruteur":
        query = query.filter(Stage.recruteur_id == current_user.id)
    elif current_user.type == "stagiaire":
        query = query.filter(Stage.stagiaire_id == current_user.id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé"
        )
    
    # Filtres de recherche
    if search:
        query = query.filter(
            (Certificat.nom_stagiaire.ilike(f"%{search}%")) |
            (Certificat.prenom_stagiaire.ilike(f"%{search}%")) |
            (Certificat.code_unique.ilike(f"%{search}%"))
        )
    
    if mention:
        query = query.filter(Certificat.mention == mention)
    
    if annee:
        from sqlalchemy import extract
        query = query.filter(extract('year', Certificat.date_generation) == annee)
    
    # Trier par date de génération (plus récents en premier)
    query = query.order_by(Certificat.date_generation.desc())
    
    certificates = query.offset(skip).limit(limit).all()
    return certificates

@router.get("/certificats/by-evaluation/{evaluation_id}", response_model=CertificatSchema)
def get_certificate_by_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Récupérer le certificat d'une évaluation spécifique."""
    
    # Vérifier que l'évaluation existe
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Évaluation non trouvée"
        )
    
    # Vérifier les permissions sur l'évaluation
    stage = evaluation.stage
    if (current_user.type == "responsable_rh" and stage.entreprise_id != current_user.entreprise_id) or \
       (current_user.type == "recruteur" and stage.recruteur_id != current_user.id) or \
       (current_user.type == "stagiaire" and stage.stagiaire_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à cette évaluation"
        )
    
    # Récupérer le certificat
    certificat = db.query(Certificat).filter(
        Certificat.evaluation_id == evaluation_id
    ).first()
    
    if not certificat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun certificat trouvé pour cette évaluation"
        )
    
    return certificat