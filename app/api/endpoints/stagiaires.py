# app/api/endpoints/stagiaires.py - NOUVEAU FICHIER
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_current_user, get_db, get_user_by_type
from app.models.utilisateur import Utilisateur
from app.models.stagiaire import Stagiaire
from app.schemas.stagiaire import (
    StagiaireProfile, 
    StagiaireProfileUpdate
)
from app.core.file_storage import save_photo_file, save_cv_file, delete_file
from app.core.security import get_password_hash

from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload

import os

router = APIRouter()

@router.get("/profile", response_model=StagiaireProfile)
def get_stagiaire_profile(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Récupérer le profil complet du stagiaire connecté."""
    
    # Récupérer le stagiaire avec tous ses détails
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil stagiaire non trouvé"
        )
    
    print(f"📄 Profil stagiaire récupéré: {stagiaire.email}")
    return stagiaire

@router.put("/profile", response_model=StagiaireProfile)
def update_stagiaire_profile(
    profile_update: StagiaireProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Mettre à jour le profil du stagiaire connecté."""
    
    # Récupérer le stagiaire
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil stagiaire non trouvé"
        )
    
    # Mettre à jour les champs modifiés
    update_data = profile_update.dict(exclude_unset=True)
    
    print(f"📝 Mise à jour profil: {list(update_data.keys())}")
    
    for field, value in update_data.items():
        if hasattr(stagiaire, field):
            setattr(stagiaire, field, value)
            print(f"  - {field}: {value}")
    
    try:
        db.commit()
        db.refresh(stagiaire)
        print(f"✅ Profil mis à jour pour: {stagiaire.email}")
        return stagiaire
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors de la mise à jour: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du profil"
        )

@router.post("/profile/upload-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Upload d'une nouvelle photo de profil pour le stagiaire."""
    
    try:
        # Récupérer le stagiaire
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
        
        if not stagiaire:
            raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
        
        # Supprimer l'ancienne photo si elle existe
        if stagiaire.photo and stagiaire.photo.startswith("photos/"):
            delete_file(f"uploads/{stagiaire.photo}")
        
        # Sauvegarder la nouvelle photo
        photo_filename = await save_photo_file(file)
        stagiaire.photo = photo_filename
        
        db.commit()
        db.refresh(stagiaire)
        
        print(f"📸 Nouvelle photo uploadée: {photo_filename}")
        
        return {
            "message": "Photo de profil mise à jour avec succès",
            "photo_filename": photo_filename,
            "photo_url": f"/uploads/{photo_filename}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Erreur upload photo: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload de la photo")

@router.post("/profile/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    analyze: bool = True,  # 🆕 Option pour analyser automatiquement
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Upload du CV pour le stagiaire avec analyse automatique des compétences."""
    
    try:
        # Récupérer le stagiaire
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
        
        if not stagiaire:
            raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
        
        # Supprimer l'ancien CV si il existe
        if stagiaire.cv_filename:
            old_cv_path = f"uploads/cv/{stagiaire.cv_filename}"
            delete_file(old_cv_path)
        
        # Sauvegarder le nouveau CV
        cv_path = await save_cv_file(file)
        
        # Extraire juste le nom du fichier du chemin complet
        import os
        cv_filename = os.path.basename(cv_path)
        stagiaire.cv_filename = cv_filename
        
        # 🆕 ANALYSE AUTOMATIQUE DU CV
        analysis_result = None
        if analyze:
            from app.services.cv_analysis_service import CVAnalysisService
            
            print(f"🔍 Démarrage analyse du CV: {cv_path}")
            analysis_result = CVAnalysisService.analyze_cv_file(cv_path)
            
            if analysis_result.get("success"):
                # Mettre à jour les compétences extraites
                CVAnalysisService.update_stagiaire_competences(
                    db, stagiaire.id, analysis_result
                )
                db.refresh(stagiaire)  # Recharger pour avoir les nouvelles compétences
        
        db.commit()
        
        response = {
            "message": "CV uploadé avec succès",
            "cv_filename": cv_filename,
            "cv_path": cv_path,
            "analysis_performed": analyze,
        }
        
        # Ajouter les résultats d'analyse si disponibles
        if analysis_result:
            if analysis_result.get("success"):
                response.update({
                    "analysis_success": True,
                    "competences_extracted": analysis_result.get("total_competences", 0),
                    "competences_found": analysis_result.get("all_competences", []),
                    "experience_level": analysis_result.get("experience_level"),
                    "analysis_summary": analysis_result.get("analysis_summary", {})
                })
                print(f"✅ Analyse réussie: {analysis_result.get('total_competences', 0)} compétences")
            else:
                response.update({
                    "analysis_success": False,
                    "analysis_error": analysis_result.get("error")
                })
                print(f"❌ Échec analyse: {analysis_result.get('error')}")
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Erreur upload CV: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload du CV")

@router.post("/profile/analyze-cv")
def analyze_existing_cv(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Analyser le CV déjà uploadé du stagiaire."""
    
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
    
    if not stagiaire.cv_filename:
        raise HTTPException(status_code=400, detail="Aucun CV n'a été uploadé")
    
    # Construire le chemin du CV
    cv_path = f"uploads/cv/{stagiaire.cv_filename}"
    
    if not os.path.exists(cv_path):
        raise HTTPException(status_code=404, detail="Fichier CV introuvable")
    
    try:
        from app.services.cv_analysis_service import CVAnalysisService
        
        print(f"🔍 Analyse du CV existant: {cv_path}")
        analysis_result = CVAnalysisService.analyze_cv_file(cv_path)
        
        if analysis_result.get("success"):
            # Mettre à jour les compétences extraites
            CVAnalysisService.update_stagiaire_competences(
                db, stagiaire.id, analysis_result
            )
            
            return {
                "message": "Analyse du CV terminée avec succès",
                "analysis_success": True,
                "competences_extracted": analysis_result.get("total_competences", 0),
                "competences_found": analysis_result.get("all_competences", []),
                "competences_by_category": analysis_result.get("competences_by_category", {}),
                "experience_level": analysis_result.get("experience_level"),
                "analysis_summary": analysis_result.get("analysis_summary", {})
            }
        else:
            return {
                "message": "Échec de l'analyse du CV",
                "analysis_success": False,
                "error": analysis_result.get("error")
            }
            
    except Exception as e:
        print(f"❌ Erreur analyse CV: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@router.get("/profile/competences")
def get_stagiaire_competences(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Récupérer toutes les compétences du stagiaire (manuelles + extraites)."""
    
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
    
    competences = stagiaire.get_all_competences()
    
    return {
        "competences_manuelles": stagiaire.competences_manuelles,
        "competences_extraites": stagiaire.competences_extraites,
        "toutes_competences": competences,
        "nombre_competences": len(competences)
    }

@router.delete("/profile/photo")
def delete_profile_photo(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Supprimer la photo de profil du stagiaire."""
    
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
    
    if stagiaire.photo:
        # Supprimer le fichier physique
        if stagiaire.photo.startswith("photos/"):
            delete_file(f"uploads/{stagiaire.photo}")
        
        # Supprimer la référence en base
        stagiaire.photo = None
        db.commit()
        
        return {"message": "Photo de profil supprimée avec succès"}
    else:
        return {"message": "Aucune photo à supprimer"}

@router.get("/recommendations")
def get_personalized_recommendations(
    limit: int = 10,
    min_score: float = 20.0,
    include_similar_profiles: bool = True,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Obtenir des recommandations d'offres personnalisées basées sur le profil et les compétences."""
    
    try:
        from app.services.recommendation_service import RecommendationService
        
        print(f"🎯 Génération de recommandations pour stagiaire {current_user.id}")
        
        # Recommandations basées sur le profil
        recommendations = RecommendationService.get_personalized_recommendations(
            db, current_user.id, limit, min_score
        )
        
        # Recommandations basées sur des profils similaires (optionnel)
        similar_recommendations = []
        if include_similar_profiles:
            similar_recommendations = RecommendationService.get_similar_profiles_recommendations(
                db, current_user.id, limit=5
            )
        
        # Résumé du profil pour contexte
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
        profile_summary = {
            "competences_count": len(stagiaire.get_all_competences()) if stagiaire else 0,
            "specialite": stagiaire.specialite if stagiaire else None,
            "niveau_etudes": stagiaire.niveau_etudes if stagiaire else None,
            "ville": stagiaire.ville if stagiaire else None,
            "has_cv": bool(stagiaire.cv_filename) if stagiaire else False
        }
        
        return {
            "recommendations": recommendations,
            "total_found": len(recommendations),
            "similar_profiles_recommendations": similar_recommendations,
            "profile_summary": profile_summary,
            "search_criteria": {
                "min_score": min_score,
                "limit": limit,
                "include_similar_profiles": include_similar_profiles
            },
            "message": f"{len(recommendations)} offres recommandées trouvées" if recommendations else "Aucune recommandation trouvée. Complétez votre profil pour de meilleurs résultats."
        }
        
    except Exception as e:
        print(f"❌ Erreur recommandations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération des recommandations"
        )

@router.get("/recommendations/analyze")
def analyze_recommendation_potential(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Analyser le potentiel de recommandation et donner des conseils pour l'améliorer."""
    
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
    
    # Analyse du profil
    analysis = {
        "profile_completeness": 0,
        "strengths": [],
        "improvements": [],
        "missing_fields": []
    }
    
    # Calcul du score de complétude
    completeness_factors = {
        "nom": bool(stagiaire.nom),
        "prenom": bool(stagiaire.prenom),
        "email": bool(stagiaire.email),
        "telephone": bool(stagiaire.telephone),
        "ville": bool(stagiaire.ville),
        "niveau_etudes": bool(stagiaire.niveau_etudes),
        "specialite": bool(stagiaire.specialite),
        "competences_manuelles": bool(stagiaire.competences_manuelles),
        "cv_uploaded": bool(stagiaire.cv_filename),
        "competences_extraites": bool(stagiaire.competences_extraites)
    }
    
    completed = sum(completeness_factors.values())
    total = len(completeness_factors)
    analysis["profile_completeness"] = round((completed / total) * 100, 1)
    
    # Forces du profil
    if stagiaire.competences_extraites and stagiaire.competences_manuelles:
        analysis["strengths"].append("Compétences bien documentées (manuelles + CV)")
    elif stagiaire.competences_extraites or stagiaire.competences_manuelles:
        analysis["strengths"].append("Compétences renseignées")
    
    if stagiaire.niveau_etudes and stagiaire.specialite:
        analysis["strengths"].append("Formation clairement définie")
    
    if stagiaire.ville:
        analysis["strengths"].append("Localisation précisée")
    
    if stagiaire.cv_filename:
        analysis["strengths"].append("CV uploadé")
    
    # Améliorations possibles
    if not stagiaire.telephone:
        analysis["missing_fields"].append("telephone")
        analysis["improvements"].append("Ajoutez votre numéro de téléphone")
    
    if not stagiaire.ville:
        analysis["missing_fields"].append("ville")
        analysis["improvements"].append("Précisez votre ville pour des recommandations géolocalisées")
    
    if not stagiaire.niveau_etudes:
        analysis["missing_fields"].append("niveau_etudes")
        analysis["improvements"].append("Indiquez votre niveau d'études")
    
    if not stagiaire.specialite:
        analysis["missing_fields"].append("specialite")
        analysis["improvements"].append("Précisez votre spécialité/domaine d'études")
    
    if not stagiaire.competences_manuelles:
        analysis["missing_fields"].append("competences_manuelles")
        analysis["improvements"].append("Listez vos compétences manuellement")
    
    if not stagiaire.cv_filename:
        analysis["missing_fields"].append("cv")
        analysis["improvements"].append("Uploadez votre CV pour une analyse automatique des compétences")
    
    if stagiaire.cv_filename and not stagiaire.competences_extraites:
        analysis["improvements"].append("Relancez l'analyse de votre CV pour extraire les compétences")
    
    # Compter les offres disponibles
    from app.models.offre import Offre
    total_offres = db.query(Offre).filter(
        Offre.est_active == True,
        Offre.date_fin >= datetime.now().date()
    ).count()
    
    return {
        "profile_analysis": analysis,
        "available_offers": total_offres,
        "recommendation": "Complétez votre profil pour de meilleures recommandations" if analysis["profile_completeness"] < 80 else "Votre profil est bien complété !",
        "next_steps": analysis["improvements"][:3]  # Top 3 améliorations
    }

@router.get("/recommendations/test-match/{offre_id}")
def test_match_with_offer(
    offre_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Tester le niveau de correspondance avec une offre spécifique."""
    
    from app.services.recommendation_service import RecommendationService
    from app.models.offre import Offre
    
    # Récupérer l'offre
    offre = db.query(Offre).options(joinedload(Offre.entreprise)).filter(
        Offre.id == offre_id
    ).first()
    
    if not offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    # Récupérer le stagiaire
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    if not stagiaire:
        raise HTTPException(status_code=404, detail="Profil stagiaire non trouvé")
    
    # Calculer les scores
    stagiaire_competences = stagiaire.get_all_competences()
    
    competence_score = RecommendationService.calculate_competence_match_score(
        stagiaire_competences, offre.competences_requises or ""
    )
    
    secteur_score = RecommendationService.calculate_secteur_match_score(
        stagiaire.specialite or "", offre.secteur
    )
    
    experience_score = RecommendationService.calculate_experience_match_score(
        stagiaire.niveau_etudes or "", offre.description
    )
    
    location_score = RecommendationService.calculate_location_match_score(
        stagiaire.ville or "", offre.localisation or ""
    )
    
    overall_score = RecommendationService.calculate_overall_match_score(
        competence_score, secteur_score, experience_score, location_score
    )
    
    # Évaluation qualitative
    if overall_score >= 80:
        recommendation = "Excellente correspondance ! Candidatez rapidement."
    elif overall_score >= 60:
        recommendation = "Bonne correspondance. Cette offre vous convient."
    elif overall_score >= 40:
        recommendation = "Correspondance moyenne. Vous pouvez tenter votre chance."
    else:
        recommendation = "Correspondance faible. Peut-être pas la meilleure option."
    
    return {
        "offre": {
            "id": offre.id,
            "titre": offre.titre,
            "entreprise": offre.entreprise.raison_social if offre.entreprise else "N/A",
            "secteur": offre.secteur,
            "localisation": offre.localisation
        },
        "match_analysis": {
            "overall_score": overall_score,
            "competence_match": competence_score,
            "secteur_match": secteur_score,
            "experience_match": experience_score,
            "location_match": location_score
        },
        "recommendation": recommendation,
        "detailed_feedback": {
            "your_competences": stagiaire_competences,
            "required_competences": offre.competences_requises,
            "your_speciality": stagiaire.specialite,
            "offer_sector": offre.secteur,
            "your_location": stagiaire.ville,
            "offer_location": offre.localisation
        }
    }

@router.get("/market-insights")
def get_market_insights(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Obtenir des insights sur le marché des stages et la position concurrentielle."""
    
    try:
        from app.services.recommendation_stats import RecommendationStatsService
        
        # Insights généraux du marché
        market_insights = RecommendationStatsService.get_market_insights(db)
        
        # Analyse de la demande en compétences
        competences_analysis = RecommendationStatsService.get_competences_demand_analysis(db)
        
        # Patterns de succès
        success_patterns = RecommendationStatsService.get_success_patterns(db)
        
        # Position personnalisée du stagiaire
        personal_position = RecommendationStatsService.get_personalized_market_position(
            db, current_user.id
        )
        
        return {
            "market_overview": market_insights,
            "competences_demand": competences_analysis,
            "success_insights": success_patterns,
            "your_position": personal_position,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_opportunities": market_insights["stats_generales"]["total_offres_actives"],
                "most_demanded_skill": competences_analysis["competences_les_plus_demandees"][0]["competence"] if competences_analysis["competences_les_plus_demandees"] else "N/A",
                "best_sector": success_patterns["secteurs_plus_accessibles"][0]["secteur"] if success_patterns["secteurs_plus_accessibles"] else "N/A",
                "your_competitiveness": personal_position.get("score_competitivite", "N/A")
            }
        }
        
    except Exception as e:
        print(f"❌ Erreur market insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération des insights marché"
        )

@router.get("/recommendations/bulk-analyze")
def bulk_analyze_recommendations(
    limit: int = 20,
    min_score: float = 30.0,
    export_format: str = "json",
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Analyser en masse toutes les offres disponibles avec scores détaillés."""
    
    try:
        from app.services.recommendation_service import RecommendationService
        from app.models.offre import Offre
        
        # Récupérer toutes les offres actives
        all_offers = db.query(Offre).options(joinedload(Offre.entreprise)).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date()
        ).all()
        
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
        if not stagiaire:
            raise HTTPException(status_code=404, detail="Profil non trouvé")
        
        stagiaire_competences = stagiaire.get_all_competences()
        
        detailed_analysis = []
        
        for offre in all_offers:
            # Calculer tous les scores
            competence_score = RecommendationService.calculate_competence_match_score(
                stagiaire_competences, offre.competences_requises or ""
            )
            secteur_score = RecommendationService.calculate_secteur_match_score(
                stagiaire.specialite or "", offre.secteur
            )
            experience_score = RecommendationService.calculate_experience_match_score(
                stagiaire.niveau_etudes or "", offre.description
            )
            location_score = RecommendationService.calculate_location_match_score(
                stagiaire.ville or "", offre.localisation or ""
            )
            overall_score = RecommendationService.calculate_overall_match_score(
                competence_score, secteur_score, experience_score, location_score
            )
            
            if overall_score >= min_score:
                detailed_analysis.append({
                    "offre_id": offre.id,
                    "titre": offre.titre,
                    "entreprise": offre.entreprise.raison_social if offre.entreprise else "N/A",
                    "secteur": offre.secteur,
                    "localisation": offre.localisation,
                    "scores": {
                        "global": overall_score,
                        "competences": competence_score,
                        "secteur": secteur_score,
                        "experience": experience_score,
                        "localisation": location_score
                    },
                    "ranking": "A" if overall_score >= 80 else "B" if overall_score >= 60 else "C",
                    "urgency": "High" if offre.date_fin <= (datetime.now().date() + timedelta(days=7)) else "Medium",
                    "competition_level": "High" if overall_score >= 70 else "Medium"  # Estimation simple
                })
        
        # Trier par score global
        detailed_analysis.sort(key=lambda x: x["scores"]["global"], reverse=True)
        
        # Limiter les résultats
        detailed_analysis = detailed_analysis[:limit]
        
        # Statistiques de l'analyse
        total_analyzed = len(all_offers)
        matching_offers = len(detailed_analysis)
        
        stats = {
            "total_offers_analyzed": total_analyzed,
            "matching_offers": matching_offers,
            "match_rate": round((matching_offers / total_analyzed) * 100, 2) if total_analyzed > 0 else 0,
            "average_score": round(sum(item["scores"]["global"] for item in detailed_analysis) / len(detailed_analysis), 2) if detailed_analysis else 0,
            "ranking_distribution": {
                "A_tier": len([item for item in detailed_analysis if item["ranking"] == "A"]),
                "B_tier": len([item for item in detailed_analysis if item["ranking"] == "B"]),
                "C_tier": len([item for item in detailed_analysis if item["ranking"] == "C"])
            }
        }
        
        return {
            "analysis_results": detailed_analysis,
            "analysis_statistics": stats,
            "recommendations": {
                "priority_applications": [item for item in detailed_analysis[:5] if item["ranking"] == "A"],
                "backup_options": [item for item in detailed_analysis if item["ranking"] == "B"][:3],
                "strategic_advice": [
                    f"Candidatez en priorité aux {stats['ranking_distribution']['A_tier']} offres de rang A",
                    f"Votre taux de correspondance est de {stats['match_rate']}%",
                    "Concentrez-vous sur les offres urgentes (High urgency)"
                ]
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Erreur bulk analyze: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'analyse en masse"
        )

@router.get("/career-guidance")
def get_career_guidance(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Obtenir des conseils de carrière personnalisés basés sur le marché et le profil."""
    
    try:
        from app.services.recommendation_service import RecommendationService
        from app.services.recommendation_stats import RecommendationStatsService
        
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
        if not stagiaire:
            raise HTTPException(status_code=404, detail="Profil non trouvé")
        
        # Analyser les compétences du marché
        market_competences = RecommendationStatsService.get_competences_demand_analysis(db)
        
        # Compétences du stagiaire
        user_competences = stagiaire.get_all_competences()
        
        # Identifier les gaps de compétences
        demanded_skills = [item["competence"] for item in market_competences["competences_les_plus_demandees"][:10]]
        missing_skills = [skill for skill in demanded_skills if skill not in [c.lower() for c in user_competences]]
        
        # Recommandations basées sur la spécialité
        specialty_advice = []
        if stagiaire.specialite:
            specialty_lower = stagiaire.specialite.lower()
            if "informatique" in specialty_lower or "développement" in specialty_lower:
                specialty_advice = [
                    "Maîtrisez Git et GitHub - essentiels pour tout développeur",
                    "Apprenez au moins un framework moderne (React, Angular, ou Vue)",
                    "Développez des compétences en bases de données (SQL)",
                    "Créez un portfolio de projets sur GitHub"
                ]
            elif "marketing" in specialty_lower or "commerce" in specialty_lower:
                specialty_advice = [
                    "Formez-vous au marketing digital et aux réseaux sociaux",
                    "Apprenez Google Analytics et les outils SEO",
                    "Développez des compétences en création de contenu",
                    "Maîtrisez les outils CRM"
                ]
            elif "design" in specialty_lower:
                specialty_advice = [
                    "Maîtrisez les outils Adobe (Photoshop, Illustrator, InDesign)",
                    "Apprenez les principes UX/UI",
                    "Créez un portfolio en ligne attractif",
                    "Familiarisez-vous avec Figma ou Sketch"
                ]
        
        # Conseils généraux adaptés au niveau
        level_advice = []
        if stagiaire.niveau_etudes:
            if "bac" in stagiaire.niveau_etudes.lower():
                level_advice = [
                    "Multipliez les stages courts pour explorer différents domaines",
                    "Développez vos soft skills : communication, travail d'équipe",
                    "Créez un réseau professionnel dès maintenant"
                ]
            elif "master" in stagiaire.niveau_etudes.lower():
                level_advice = [
                    "Visez des stages avec responsabilités",
                    "Recherchez des mentors dans votre domaine",
                    "Préparez-vous pour des postes junior post-stage"
                ]
        
        # Analyse des tendances du marché
        market_trends = {
            "secteurs_en_croissance": ["Tech", "E-commerce", "Digital", "Data Science"],
            "competences_emergentes": ["Intelligence Artificielle", "Cybersécurité", "Cloud Computing"],
            "formats_populaires": ["Télétravail", "Hybride", "Stage long (6 mois+)"]
        }
        
        # Score de préparation au marché
        preparation_score = 0
        if stagiaire.cv_filename:
            preparation_score += 25
        if stagiaire.competences_extraites or stagiaire.competences_manuelles:
            preparation_score += 25
        if stagiaire.specialite:
            preparation_score += 20
        if stagiaire.niveau_etudes:
            preparation_score += 15
        if stagiaire.ville:
            preparation_score += 15
        
        return {
            "career_assessment": {
                "preparation_score": preparation_score,
                "profile_strength": "Excellent" if preparation_score >= 80 else "Bon" if preparation_score >= 60 else "À améliorer",
                "missing_competences": missing_skills[:5],
                "your_competences": user_competences
            },
            "personalized_advice": {
                "specialty_specific": specialty_advice,
                "level_appropriate": level_advice,
                "immediate_actions": [
                    "Complétez votre profil à 100%" if preparation_score < 100 else "Candidatez aux offres recommandées",
                    f"Développez ces compétences demandées: {', '.join(missing_skills[:3])}" if missing_skills else "Maintenez vos compétences à jour",
                    "Uploadez votre CV pour une meilleure analyse" if not stagiaire.cv_filename else "Mettez à jour votre CV régulièrement"
                ]
            },
            "market_trends": market_trends,
            "success_pathway": {
                "short_term": [
                    "Complétez votre profil",
                    "Postulez à 5-10 offres par semaine",
                    "Développez 2-3 compétences manquantes"
                ],
                "medium_term": [
                    "Réalisez un stage réussi",
                    "Construisez votre réseau professionnel",
                    "Obtenez des recommandations"
                ],
                "long_term": [
                    "Décrochez un emploi dans votre domaine",
                    "Devenez expert dans votre spécialité",
                    "Encadrez d'autres stagiaires"
                ]
            },
            "learning_resources": {
                "online_platforms": ["Coursera", "Udemy", "LinkedIn Learning"],
                "free_resources": ["YouTube", "FreeCodeCamp", "Khan Academy"],
                "certifications": ["Google", "Microsoft", "AWS", "Salesforce"]
            }
        }
        
    except Exception as e:
        print(f"❌ Erreur career guidance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération des conseils carrière"
        )

@router.get("/profile/stats")
def get_stagiaire_stats(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
):
    """Statistiques du profil stagiaire."""
    
    from app.models.candidature import Candidature
    from app.models.stage import Stage
    
    stagiaire = db.query(Stagiaire).filter(Stagiaire.id == current_user.id).first()
    
    # Compter les candidatures
    total_candidatures = db.query(Candidature).filter(
        Candidature.stagiaire_id == current_user.id
    ).count()
    
    # Compter les stages
    total_stages = db.query(Stage).filter(
        Stage.stagiaire_id == current_user.id
    ).count()
    
    # Compter les compétences
    competences = stagiaire.get_all_competences() if stagiaire else []
    
    return {
        "candidatures_soumises": total_candidatures,
        "stages_effectues": total_stages,
        "competences_declarees": len(competences),
        "profil_complete": bool(
            stagiaire and 
            stagiaire.telephone and 
            stagiaire.niveau_etudes and 
            stagiaire.competences_manuelles
        )
    }

# ////////////////////////////////////////////////////////////:



# Dans app/api/endpoints/stagiaires.py - AJOUTEZ CET ENDPOINT

# @router.get("/test-recommendations")
# def test_recommendations_system(
#     min_score: float = 10.0,
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
# ):
#     """Endpoint de test pour le système de recommandations."""
    
#     try:
#         from app.services.recommendation_service import RecommendationService
        
#         print("🚀 DÉBUT DU TEST DU SYSTÈME DE RECOMMANDATIONS")
#         print("=" * 60)
        
#         # Test avec la nouvelle logique
#         recommendations = RecommendationService.get_personalized_recommendations(
#             db, current_user.id, limit=10, min_score=min_score
#         )
        
#         print("=" * 60)
#         print(f"🎯 RÉSULTAT: {len(recommendations)} recommandations trouvées")
        
#         return {
#             "status": "success",
#             "test_results": {
#                 "recommendations_found": len(recommendations),
#                 "min_score_used": min_score,
#                 "recommendations": recommendations
#             },
#             "debug_info": {
#                 "stagiaire_id": current_user.id,
#                 "timestamp": datetime.now().isoformat()
#             }
#         }
        
#     except Exception as e:
#         print(f"❌ ERREUR DANS LE TEST: {str(e)}")
#         import traceback
#         traceback.print_exc()
        
#         return {
#             "status": "error",
#             "error": str(e),
#             "traceback": traceback.format_exc()
#         }

# @router.get("/test-single-match/{offre_id}")
# def test_single_match(
#     offre_id: int,
#     db: Session = Depends(get_db),
#     current_user: Utilisateur = Depends(get_user_by_type("stagiaire"))
# ):
#     """Tester le matching avec une offre spécifique."""
    
#     try:
#         from app.services.recommendation_service import RecommendationService
        
#         result = RecommendationService.test_single_match(
#             db, current_user.id, offre_id
#         )
        
#         return {
#             "status": "success",
#             "match_test": result
#         }
        
#     except Exception as e:
#         return {
#             "status": "error", 
#             "error": str(e)
#         }