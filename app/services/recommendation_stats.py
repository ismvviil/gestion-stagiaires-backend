# app/services/recommendation_stats.py - NOUVEAU FICHIER
from sqlalchemy.orm import Session
from sqlalchemy import func, desc , case  
from typing import Dict, List
from app.models.offre import Offre
from app.models.candidature import Candidature, StatusCandidature
from app.models.stagiaire import Stagiaire
from datetime import datetime, timedelta
class RecommendationStatsService:
    """Service pour les statistiques des recommandations."""
    
    @classmethod
    def get_competences_demand_analysis(cls, db: Session) -> Dict:
        """Analyser la demande en compétences sur le marché."""
        
        # Récupérer toutes les offres actives avec leurs compétences
        offres = db.query(Offre.competences_requises).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date(),
            Offre.competences_requises.isnot(None)
        ).all()
        
        # Compter les compétences les plus demandées
        competences_count = {}
        
        # Compétences techniques populaires à rechercher
        tech_keywords = [
            "python", "javascript", "java", "react", "node.js", "sql", "html", "css",
            "angular", "vue", "php", "c++", "c#", "django", "flask", "spring",
            "mysql", "postgresql", "mongodb", "git", "docker", "aws", "azure",
            "machine learning", "data science", "artificial intelligence", "ai",
            "mobile", "android", "ios", "flutter", "react native"
        ]
        
        for offre in offres:
            if offre.competences_requises:
                text = offre.competences_requises.lower()
                for keyword in tech_keywords:
                    if keyword in text:
                        competences_count[keyword] = competences_count.get(keyword, 0) + 1
        
        # Trier par popularité
        top_competences = sorted(
            competences_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:15]
        
        return {
            "competences_les_plus_demandees": [
                {"competence": comp, "nombre_offres": count, "popularite": round((count/len(offres))*100, 1)}
                for comp, count in top_competences
            ],
            "total_offres_analysees": len(offres),
            "recommandation": "Développez ces compétences pour maximiser vos opportunités"
        }
    
    @classmethod
    def get_success_patterns(cls, db: Session) -> Dict:
        """Analyser les patterns de succès des candidatures."""
        
        # Candidatures acceptées vs total
        total_candidatures = db.query(Candidature).count()
        candidatures_acceptees = db.query(Candidature).filter(
            Candidature.status == StatusCandidature.ACCEPTEE
        ).count()
        
        taux_succes_global = round((candidatures_acceptees / total_candidatures) * 100, 2) if total_candidatures > 0 else 0
        
        # Secteurs avec le meilleur taux d'acceptation
        # secteurs_succes = db.query(
        #     Offre.secteur,
        #     func.count(Candidature.id).label('total_candidatures'),
        #     # func.sum(func.case([(Candidature.status == StatusCandidature.ACCEPTEE, 1)], else_=0)).label('acceptees')
        #     func.sum(case([(Candidature.status == StatusCandidature.ACCEPTEE, 1)], else_=0)).label('acceptees')
        # ).join(Candidature).group_by(Offre.secteur).having(func.count(Candidature.id) >= 5).all()
        
        secteurs_succes = db.query(
            Offre.secteur,
            func.count(Candidature.id).label('total_candidatures'),
            func.sum(case((Candidature.status == StatusCandidature.ACCEPTEE, 1), else_=0)).label('acceptees')
        ).join(Candidature).group_by(Offre.secteur).having(func.count(Candidature.id) >= 5).all()
        secteurs_analysis = []
        for secteur_stat in secteurs_succes:
            taux = round((secteur_stat.acceptees / secteur_stat.total_candidatures) * 100, 2)
            secteurs_analysis.append({
                "secteur": secteur_stat.secteur,
                "taux_succes": taux,
                "total_candidatures": secteur_stat.total_candidatures
            })
        
        # Trier par taux de succès
        secteurs_analysis.sort(key=lambda x: x["taux_succes"], reverse=True)
        
        # Analyse des profils gagnants
        stagiaires_succes = db.query(Stagiaire).join(Candidature).filter(
            Candidature.status == StatusCandidature.ACCEPTEE
        ).distinct().all()
        
        # Spécialités les plus réussies
        specialites_count = {}
        niveaux_count = {}
        
        for stagiaire in stagiaires_succes:
            if stagiaire.specialite:
                specialites_count[stagiaire.specialite] = specialites_count.get(stagiaire.specialite, 0) + 1
            if stagiaire.niveau_etudes:
                niveaux_count[stagiaire.niveau_etudes] = niveaux_count.get(stagiaire.niveau_etudes, 0) + 1
        
        return {
            "taux_succes_global": taux_succes_global,
            "secteurs_plus_accessibles": secteurs_analysis[:5],
            "specialites_gagnantes": sorted(specialites_count.items(), key=lambda x: x[1], reverse=True)[:5],
            "niveaux_etudes_succes": sorted(niveaux_count.items(), key=lambda x: x[1], reverse=True),
            "conseils": [
                f"Le secteur '{secteurs_analysis[0]['secteur']}' a le meilleur taux de succès" if secteurs_analysis else "Variez vos candidatures",
                "Complétez votre profil pour augmenter vos chances",
                "Adaptez votre CV aux compétences demandées"
            ]
        }
    
    @classmethod
    def get_personalized_market_position(cls, db: Session, stagiaire_id: int) -> Dict:
        """Analyser la position du stagiaire sur le marché."""
        
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
        if not stagiaire:
            return {"error": "Stagiaire non trouvé"}
        
        # Comparer avec des profils similaires
        profils_similaires = db.query(Stagiaire).filter(
            Stagiaire.id != stagiaire_id,
            Stagiaire.specialite == stagiaire.specialite,
            Stagiaire.niveau_etudes == stagiaire.niveau_etudes
        ).all()
        
        # Analyser la concurrence
        if profils_similaires:
            # Compétences moyennes des profils similaires
            competences_autres = []
            for profil in profils_similaires:
                competences_autres.extend(profil.get_all_competences())
            
            competences_stagiaire = stagiaire.get_all_competences()
            
            # Avantages concurrentiels
            competences_uniques = [
                comp for comp in competences_stagiaire 
                if competences_stagiaire.count(comp) > competences_autres.count(comp)
            ]
            
            # Analyse du marché pour son profil
            offres_compatibles = db.query(Offre).filter(
                Offre.est_active == True,
                Offre.date_fin >= datetime.now().date(),
                Offre.secteur.ilike(f"%{stagiaire.specialite}%") if stagiaire.specialite else True
            ).count()
            
            candidatures_concurrentes = db.query(Candidature).join(Offre).join(Stagiaire).filter(
                Offre.est_active == True,
                Stagiaire.specialite == stagiaire.specialite,
                Stagiaire.niveau_etudes == stagiaire.niveau_etudes,
                Stagiaire.id != stagiaire_id
            ).count()
            
            ratio_concurrence = round(candidatures_concurrentes / offres_compatibles, 2) if offres_compatibles > 0 else 0
            
            return {
                "profils_similaires_count": len(profils_similaires),
                "offres_compatibles": offres_compatibles,
                "niveau_concurrence": "Élevé" if ratio_concurrence > 2 else "Modéré" if ratio_concurrence > 1 else "Faible",
                "competences_uniques": competences_uniques[:5],
                "recommandations_strategiques": [
                    "Mettez en avant vos compétences uniques" if competences_uniques else "Développez des compétences distinctives",
                    f"Il y a {offres_compatibles} offres compatibles avec votre profil",
                    f"Vous êtes en concurrence avec {len(profils_similaires)} profils similaires"
                ],
                "score_competitivite": min(100, max(0, 100 - (ratio_concurrence * 20)))
            }
        else:
            return {
                "profils_similaires_count": 0,
                "message": "Profil unique ! Peu de concurrence directe.",
                "recommandations_strategiques": [
                    "Votre profil est peu commun, c'est un avantage",
                    "Explorez des secteurs variés",
                    "Mettez en avant votre originalité"
                ],
                "score_competitivite": 85
            }
        
    @classmethod
    def get_market_insights(cls, db: Session) -> Dict:
        """Obtenir des insights sur le marché des stages."""
        
        # Offres actives par secteur
        secteurs_stats = db.query(
            Offre.secteur,
            func.count(Offre.id).label('count')
        ).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date()
        ).group_by(Offre.secteur).order_by(desc('count')).limit(10).all()
        
        # Types de stages les plus demandés
        types_stats = db.query(
            Offre.type_stage,
            func.count(Offre.id).label('count')
        ).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date()
        ).group_by(Offre.type_stage).order_by(desc('count')).all()
        
        # Localisation populaires
        locations_stats = db.query(
            Offre.localisation,
            func.count(Offre.id).label('count')
        ).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date(),
            Offre.localisation.isnot(None)
        ).group_by(Offre.localisation).order_by(desc('count')).limit(10).all()
        
        # Taux de candidature global
        total_offres = db.query(Offre).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date()
        ).count()
        
        total_candidatures = db.query(Candidature).join(Offre).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date()
        ).count()
        
        taux_candidature = round((total_candidatures / total_offres) * 100, 2) if total_offres > 0 else 0
        
        return {
            "secteurs_populaires": [
                {"secteur": stat.secteur, "nombre_offres": stat.count}
                for stat in secteurs_stats
            ],
            "types_stages": [
                {"type": stat.type_stage, "nombre_offres": stat.count}
                for stat in types_stats
            ],
            "localisations_populaires": [
                {"ville": stat.localisation, "nombre_offres": stat.count}
                for stat in locations_stats
            ],
            "stats_generales": {
                "total_offres_actives": total_offres,
                "total_candidatures": total_candidatures,
                "taux_candidature_moyen": taux_candidature
            }
        }
    
    