# app/services/recommendation_service.py - NOUVEAU FICHIER
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Optional, Tuple
from app.models.stagiaire import Stagiaire
from app.models.offre import Offre
from app.models.candidature import Candidature
from app.models.entreprise import Entreprise
import re
from datetime import datetime, timedelta

class RecommendationService:
    """Service pour recommander des offres personnalisées aux stagiaires."""
    
    @classmethod
    def calculate_competence_match_score(cls, stagiaire_competences: List[str], offre_competences: str) -> float:
        """Calculer le score de correspondance des compétences (0-100)."""
        if not stagiaire_competences or not offre_competences:
            return 0.0
        
        # Nettoyer et normaliser les compétences
        stagiaire_comp_clean = [comp.lower().strip() for comp in stagiaire_competences if comp.strip()]
        
        # Extraire les compétences de l'offre
        offre_comp_text = offre_competences.lower()
        offre_comp_words = re.findall(r'\b\w+\b', offre_comp_text)
        
        if not stagiaire_comp_clean or not offre_comp_words:
            return 0.0
        
        # Compter les correspondances
        matches = 0
        total_offre_competences = 0
        
        # Créer des variations de mots-clés pour une meilleure correspondance
        for stagiaire_comp in stagiaire_comp_clean:
            # Recherche exacte
            if stagiaire_comp in offre_comp_text:
                matches += 2  # Correspondance exacte vaut plus
            # Recherche partielle (mots contenus)
            elif any(word in stagiaire_comp or stagiaire_comp in word for word in offre_comp_words):
                matches += 1
        
        # Estimer le nombre total de compétences demandées
        # (approximation basée sur la longueur du texte)
        total_offre_competences = max(len(offre_comp_words) // 3, 1)
        
        # Calculer le score (plafonné à 100)
        score = min((matches / total_offre_competences) * 100, 100)
        return round(score, 2)

    @classmethod
    def calculate_competence_match_score(cls, stagiaire_competences: List[str], offre_competences: str) -> float:
        """Calculer le score de correspondance des compétences (0-100) - VERSION CORRIGÉE."""
        if not stagiaire_competences or not offre_competences:
            return 0.0
    
        # Nettoyer et normaliser les compétences
        stagiaire_comp_clean = [comp.lower().strip() for comp in stagiaire_competences if comp.strip()]
    
        # Extraire les compétences de l'offre - CORRECTION ICI
        offre_comp_text = offre_competences.lower()
    
        # ✅ NOUVELLE LOGIQUE : Diviser par virgules ET espaces
        import re
        # Séparer par virgules, puis nettoyer
        offre_comp_list = [comp.strip() for comp in re.split(r'[,;]', offre_comp_text) if comp.strip()]
    
        # Si pas de virgules, séparer par espaces pour les mots individuels
        if len(offre_comp_list) <= 1:
            offre_comp_list = [comp.strip() for comp in offre_comp_text.split() if comp.strip()]
    
        print(f"🔍 DEBUG Compétences:")
        print(f"  Stagiaire: {stagiaire_comp_clean[:5]}... (total: {len(stagiaire_comp_clean)})")
        print(f"  Offre brute: {offre_comp_text}")
        print(f"  Offre parsée: {offre_comp_list}")
    
        if not stagiaire_comp_clean or not offre_comp_list:
            return 0.0
    
        # Compter les correspondances - LOGIQUE AMÉLIORÉE
        matches = 0
        total_offre_competences = len(offre_comp_list)
        matched_skills = []
    
        for offre_comp in offre_comp_list:
            offre_comp_clean = offre_comp.lower().strip()
        
            # Recherche de correspondance
            found_match = False
        
            for stagiaire_comp in stagiaire_comp_clean:
                stagiaire_comp_clean = stagiaire_comp.lower().strip()
            
                # 1. Correspondance exacte
                if stagiaire_comp_clean == offre_comp_clean:
                    matches += 3  # Correspondance exacte = 3 points
                    matched_skills.append(f"{stagiaire_comp_clean} (exact)")
                    found_match = True
                    break
                
                # 2. Correspondance partielle (contient)
                elif (len(offre_comp_clean) > 3 and offre_comp_clean in stagiaire_comp_clean) or \
                    (len(stagiaire_comp_clean) > 3 and stagiaire_comp_clean in offre_comp_clean):
                    matches += 2  # Correspondance partielle = 2 points
                    matched_skills.append(f"{stagiaire_comp_clean} ≈ {offre_comp_clean}")
                    found_match = True
                    break
                
                # 3. Correspondance de mots-clés
                elif any(word in stagiaire_comp_clean for word in offre_comp_clean.split()) or \
                    any(word in offre_comp_clean for word in stagiaire_comp_clean.split()):
                    matches += 1  # Correspondance de mots = 1 point
                    matched_skills.append(f"{stagiaire_comp_clean} ~ {offre_comp_clean}")
                    found_match = True
                    break
    
        # Calculer le score sur base 100
        max_possible_score = total_offre_competences * 3  # Si tout était exact
        score = min((matches / max_possible_score) * 100, 100) if max_possible_score > 0 else 0
    
        print(f"  Matches trouvés: {matches}/{max_possible_score} = {score:.1f}%")
        print(f"  Détails matches: {matched_skills[:3]}")
    
        return round(score, 2)
    
    @classmethod
    def calculate_secteur_match_score(cls, stagiaire_specialite: str, offre_secteur: str) -> float:
        """Calculer le score de correspondance du secteur (0-100)."""
        if not stagiaire_specialite or not offre_secteur:
            return 0.0
        
        specialite_clean = stagiaire_specialite.lower().strip()
        secteur_clean = offre_secteur.lower().strip()
        
        # Correspondance exacte
        if specialite_clean == secteur_clean:
            return 100.0
        
        # Correspondance partielle
        if specialite_clean in secteur_clean or secteur_clean in specialite_clean:
            return 75.0
        
        # Correspondances par domaines
        tech_domains = ["informatique", "développement", "programmation", "logiciel", "numérique", "digital"]
        business_domains = ["commerce", "marketing", "vente", "business", "gestion", "management"]
        design_domains = ["design", "graphisme", "créatif", "ux", "ui", "web design"]
        
        def is_in_domain(text, domains):
            return any(domain in text for domain in domains)
        
        # Si les deux sont dans le même domaine général
        for domain_group in [tech_domains, business_domains, design_domains]:
            if is_in_domain(specialite_clean, domain_group) and is_in_domain(secteur_clean, domain_group):
                return 50.0
        
        return 0.0
    
    @classmethod
    def calculate_experience_match_score(cls, stagiaire_niveau: str, offre_description: str) -> float:
        """Calculer le score de correspondance du niveau d'expérience (0-100)."""
        if not stagiaire_niveau or not offre_description:
            return 50.0  # Score neutre si pas d'info
        
        niveau_clean = stagiaire_niveau.lower()
        description_clean = offre_description.lower()
        
        # Indicateurs de niveau dans l'offre
        junior_indicators = ["junior", "débutant", "stage", "étudiant", "apprenti", "première expérience"]
        senior_indicators = ["senior", "expérimenté", "confirmé", "expert", "lead", "chef"]
        
        is_junior_offre = any(indicator in description_clean for indicator in junior_indicators)
        is_senior_offre = any(indicator in description_clean for indicator in senior_indicators)
        
        # Correspondance niveau stagiaire vs offre
        if "bac" in niveau_clean or "licence" in niveau_clean:
            return 90.0 if is_junior_offre else 60.0
        elif "master" in niveau_clean or "ingénieur" in niveau_clean:
            if is_senior_offre:
                return 85.0
            elif is_junior_offre:
                return 70.0
            else:
                return 80.0  # Offre intermédiaire
        
        return 50.0  # Score par défaut
    
    @classmethod
    def calculate_location_match_score(cls, stagiaire_ville: str, offre_localisation: str) -> float:
        """Calculer le score de correspondance géographique (0-100)."""
        if not stagiaire_ville or not offre_localisation:
            return 50.0  # Score neutre
        
        ville_clean = stagiaire_ville.lower().strip()
        localisation_clean = offre_localisation.lower().strip()
        
        # Correspondance exacte
        if ville_clean == localisation_clean:
            return 100.0
        
        # Correspondance partielle
        if ville_clean in localisation_clean or localisation_clean in ville_clean:
            return 80.0
        
        # Grandes villes proches (logique simplifiée)
        grandes_villes_maroc = {
            "casablanca": ["rabat", "mohammedia"],
            "rabat": ["casablanca", "salé"],
            "marrakech": ["casablanca"],
            "fès": ["meknes"],
            "tanger": ["tétouan"]
        }
        
        for ville, villes_proches in grandes_villes_maroc.items():
            if ville_clean == ville and any(v in localisation_clean for v in villes_proches):
                return 60.0
            if any(v == ville_clean for v in villes_proches) and ville in localisation_clean:
                return 60.0
        
        # Remote/télétravail
        if "remote" in localisation_clean or "télétravail" in localisation_clean or "distance" in localisation_clean:
            return 90.0
        
        return 20.0  # Villes éloignées
    
    @classmethod
    def calculate_overall_match_score(cls, competence_score: float, secteur_score: float, 
                                    experience_score: float, location_score: float) -> float:
        """Calculer le score global de correspondance avec pondération."""
        # Pondération des critères
        weights = {
            "competences": 0.4,    # 40% - Le plus important
            "secteur": 0.25,       # 25%
            "experience": 0.20,    # 20%
            "location": 0.15       # 15%
        }
        
        overall_score = (
            competence_score * weights["competences"] +
            secteur_score * weights["secteur"] +
            experience_score * weights["experience"] +
            location_score * weights["location"]
        )
        
        return round(overall_score, 2)
    
    @classmethod
    def get_personalized_recommendations(
        cls, 
        db: Session, 
        stagiaire_id: int, 
        limit: int = 10,
        min_score: float = 20.0
    ) -> List[Dict]:
        """Obtenir des recommandations personnalisées pour un stagiaire."""
        
        # Récupérer le stagiaire avec ses compétences
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
        
        if not stagiaire:
            return []
        
        # Récupérer toutes les compétences du stagiaire
        stagiaire_competences = stagiaire.get_all_competences()
        
        # Récupérer les candidatures déjà soumises pour les exclure
        candidatures_existantes = db.query(Candidature.offre_id).filter(
            Candidature.stagiaire_id == stagiaire_id
        ).subquery()
        
        # Récupérer les offres actives (pas encore candidaté)
        offres_query = db.query(Offre).options(
            joinedload(Offre.entreprise)
        ).filter(
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date(),  # Offres non expirées
            ~Offre.id.in_(candidatures_existantes)     # Pas déjà candidaté
        )
        
        offres = offres_query.all()
        
        print(f"🔍 Analyse de {len(offres)} offres pour stagiaire {stagiaire_id}")
        print(f"📊 Compétences stagiaire: {stagiaire_competences}")
        
        recommendations = []
        
        for offre in offres:
            # Calculer les scores de correspondance
            competence_score = cls.calculate_competence_match_score(
                stagiaire_competences, 
                offre.competences_requises or ""
            )
            
            secteur_score = cls.calculate_secteur_match_score(
                stagiaire.specialite or "", 
                offre.secteur
            )
            
            experience_score = cls.calculate_experience_match_score(
                stagiaire.niveau_etudes or "", 
                offre.description
            )
            
            location_score = cls.calculate_location_match_score(
                stagiaire.ville or "", 
                offre.localisation or ""
            )
            
            # Score global
            overall_score = cls.calculate_overall_match_score(
                competence_score, secteur_score, experience_score, location_score
            )
            
            # Garder seulement les offres avec un score minimum
            if overall_score >= min_score:
                recommendation = {
                    "offre_id": offre.id,
                    "titre": offre.titre,
                    "entreprise_nom": offre.entreprise.raison_social if offre.entreprise else "N/A",
                    "secteur": offre.secteur,
                    "localisation": offre.localisation,
                    "type_stage": offre.type_stage,
                    "date_debut": offre.date_debut.isoformat(),
                    "date_fin": offre.date_fin.isoformat(),
                    "description": offre.description[:200] + "..." if len(offre.description) > 200 else offre.description,
                    
                    # Scores détaillés
                    "match_score": overall_score,
                    "competence_match": competence_score,
                    "secteur_match": secteur_score,
                    "experience_match": experience_score,
                    "location_match": location_score,
                    
                    # Métadonnées
                    "recommendation_reasons": cls._get_recommendation_reasons(
                        competence_score, secteur_score, experience_score, location_score
                    ),
                    "created_at": offre.created_at.isoformat() if offre.created_at else None
                }
                
                recommendations.append(recommendation)
        
        # Trier par score décroissant
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Limiter le nombre de résultats
        recommendations = recommendations[:limit]
        
        print(f"✅ {len(recommendations)} recommandations générées")
        if recommendations:
            print(f"🎯 Meilleur score: {recommendations[0]['match_score']}%")
        
        return recommendations
    
    @classmethod
    def _get_recommendation_reasons(cls, comp_score: float, sect_score: float, 
                                  exp_score: float, loc_score: float) -> List[str]:
        """Générer les raisons de la recommandation."""
        reasons = []
        
        if comp_score >= 70:
            reasons.append("Excellente correspondance des compétences")
        elif comp_score >= 40:
            reasons.append("Bonne correspondance des compétences")
        
        if sect_score >= 70:
            reasons.append("Secteur parfaitement adapté")
        elif sect_score >= 40:
            reasons.append("Secteur compatible")
        
        if exp_score >= 70:
            reasons.append("Niveau d'expérience approprié")
        
        if loc_score >= 80:
            reasons.append("Localisation idéale")
        elif loc_score >= 50:
            reasons.append("Localisation accessible")
        
        if not reasons:
            reasons.append("Opportunité intéressante à explorer")
        
        return reasons
    
    @classmethod
    def get_similar_profiles_recommendations(cls, db: Session, stagiaire_id: int, limit: int = 5) -> List[Dict]:
        """Recommandations basées sur des profils similaires (collaborative filtering simple)."""
        
        # Récupérer le stagiaire actuel
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
        if not stagiaire:
            return []
        
        # Trouver des stagiaires avec des profils similaires
        stagiaires_similaires = db.query(Stagiaire).filter(
            Stagiaire.id != stagiaire_id,
            Stagiaire.specialite == stagiaire.specialite,
            Stagiaire.niveau_etudes == stagiaire.niveau_etudes
        ).limit(10).all()
        
        if not stagiaires_similaires:
            return []
        
        # Récupérer les offres auxquelles ces stagiaires ont candidaté avec succès
        from app.models.candidature import StatusCandidature
        
        offres_similaires = db.query(Offre).join(Candidature).filter(
            Candidature.stagiaire_id.in_([s.id for s in stagiaires_similaires]),
            Candidature.status == StatusCandidature.ACCEPTEE,
            Offre.est_active == True,
            Offre.date_fin >= datetime.now().date()
        ).distinct().limit(limit).all()
        
        recommendations = []
        for offre in offres_similaires:
            recommendations.append({
                "offre_id": offre.id,
                "titre": offre.titre,
                "entreprise_nom": offre.entreprise.raison_social if offre.entreprise else "N/A",
                "secteur": offre.secteur,
                "reason": "Recommandé par des profils similaires"
            })
        
        return recommendations
    
    
        
        
        
# app/services/recommendation_service.py - VERSION COMPLÈTE CORRIGÉE
# from sqlalchemy.orm import Session, joinedload
# from typing import List, Dict, Optional, Tuple
# from app.models.stagiaire import Stagiaire
# from app.models.offre import Offre
# from app.models.candidature import Candidature
# from app.models.entreprise import Entreprise
# import re
# from datetime import datetime, timedelta

# class RecommendationService:
#     """Service pour recommander des offres personnalisées aux stagiaires."""
    
#     @classmethod
#     def get_personalized_recommendations(
#         cls, 
#         db: Session, 
#         stagiaire_id: int, 
#         limit: int = 10,
#         min_score: float = 20.0
#     ) -> List[Dict]:
#         """NOUVELLE VERSION - Recommandations personnalisées optimisées."""
        
#         # Récupérer le stagiaire
#         stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
#         if not stagiaire:
#             print(f"❌ Stagiaire {stagiaire_id} non trouvé")
#             return []
        
#         # Récupérer toutes les compétences
#         stagiaire_competences = stagiaire.get_all_competences()
#         print(f"🔍 Génération recommandations pour stagiaire {stagiaire_id}")
#         print(f"📊 Compétences: {len(stagiaire_competences)} trouvées")
#         print(f"📍 Profil: {stagiaire.specialite} - {stagiaire.niveau_etudes} - {stagiaire.ville}")
        
#         # ✅ NOUVEAU : Récupérer candidatures avec gestion d'erreur
#         candidatures_existantes_ids = []
#         try:
#             candidatures_existantes = db.query(Candidature.offre_id).filter(
#                 Candidature.stagiaire_id == stagiaire_id
#             ).all()
#             candidatures_existantes_ids = [c.offre_id for c in candidatures_existantes]
#             print(f"📋 Candidatures existantes: {len(candidatures_existantes_ids)}")
#         except Exception as e:
#             print(f"⚠️ Erreur candidatures existantes: {e}")
#             candidatures_existantes_ids = []
        
#         # ✅ NOUVEAU : Récupérer offres avec filtre moins strict
#         try:
#             # Date limite plus souple : 7 jours dans le passé
#             date_limite = datetime.now().date() - timedelta(days=7)
            
#             offres_query = db.query(Offre).options(joinedload(Offre.entreprise)).filter(
#                 Offre.est_active == True,
#                 Offre.date_fin >= date_limite  # Plus souple
#             )
            
#             # Exclure seulement si on a des candidatures
#             if candidatures_existantes_ids:
#                 offres_query = offres_query.filter(~Offre.id.in_(candidatures_existantes_ids))
#                 print(f"🚫 Exclusion de {len(candidatures_existantes_ids)} offres déjà candidatées")
            
#             offres = offres_query.all()
#             print(f"🎯 Offres à analyser: {len(offres)}")
            
#         except Exception as e:
#             print(f"❌ Erreur récupération offres: {e}")
#             return []
        
#         if not offres:
#             print("⚠️ Aucune offre disponible")
#             return []
        
#         recommendations = []
        
#         for offre in offres:
#             try:
#                 # ✅ NOUVEAU : Calculs de scores améliorés
#                 scores = cls._calculate_all_scores(stagiaire, offre, stagiaire_competences)
                
#                 print(f"📈 Offre {offre.id} ({offre.titre[:30]}...): "
#                       f"Comp={scores['competence']:.1f}%, "
#                       f"Sect={scores['secteur']:.1f}%, "
#                       f"Global={scores['overall']:.1f}%")
                
#                 if scores['overall'] >= min_score:
#                     recommendation = cls._build_recommendation_dict(offre, scores)
#                     recommendations.append(recommendation)
                    
#             except Exception as e:
#                 print(f"❌ Erreur calcul pour offre {offre.id}: {e}")
#                 continue
        
#         # Trier et limiter
#         recommendations.sort(key=lambda x: x["match_score"], reverse=True)
#         recommendations = recommendations[:limit]
        
#         print(f"✅ {len(recommendations)} recommandations générées (seuil: {min_score}%)")
#         if recommendations:
#             print(f"🏆 Meilleur score: {recommendations[0]['match_score']}%")
        
#         return recommendations

#     @classmethod
#     def _calculate_all_scores(cls, stagiaire: Stagiaire, offre: Offre, stagiaire_competences: List[str]) -> Dict[str, float]:
#         """Calculer tous les scores pour une offre."""
        
#         # Score compétences AMÉLIORÉ
#         competence_score = cls._calculate_competence_score_improved(
#             stagiaire_competences, 
#             offre.competences_requises or ""
#         )
        
#         # Score secteur AMÉLIORÉ  
#         secteur_score = cls._calculate_secteur_score_improved(
#             stagiaire.specialite or "", 
#             offre.secteur or ""
#         )
        
#         # Score expérience simplifié
#         experience_score = cls._calculate_experience_score_simple(
#             stagiaire.niveau_etudes or ""
#         )
        
#         # Score localisation
#         location_score = cls._calculate_location_score_improved(
#             stagiaire.ville or "", 
#             offre.localisation or ""
#         )
        
#         # Score global avec pondération équilibrée
#         overall_score = (
#             competence_score * 0.35 +
#             secteur_score * 0.30 +
#             experience_score * 0.20 +
#             location_score * 0.15
#         )
        
#         return {
#             'competence': round(competence_score, 2),
#             'secteur': round(secteur_score, 2), 
#             'experience': round(experience_score, 2),
#             'location': round(location_score, 2),
#             'overall': round(overall_score, 2)
#         }

#     @classmethod
#     def _calculate_competence_score_improved(cls, stagiaire_competences: List[str], offre_competences: str) -> float:
#         """Calcul amélioré du score de compétences."""
#         if not stagiaire_competences or not offre_competences:
#             return 30.0  # Score de base plus généreux
        
#         # Nettoyer les compétences
#         stagiaire_comp_clean = {comp.lower().strip() for comp in stagiaire_competences if comp.strip()}
        
#         # Parser les compétences de l'offre
#         offre_comp_text = offre_competences.lower()
        
#         # Diviser par virgules, points-virgules
#         offre_comp_list = re.split(r'[,;]', offre_comp_text)
#         offre_comp_list = [comp.strip() for comp in offre_comp_list if comp.strip()]
        
#         # Si pas de séparateurs, diviser par espaces  
#         if len(offre_comp_list) <= 1:
#             offre_comp_list = offre_comp_text.split()
#             offre_comp_list = [comp.strip() for comp in offre_comp_list if len(comp.strip()) > 2]
        
#         if not offre_comp_list:
#             return 50.0  # Score neutre si pas de compétences parsées
        
#         # DEBUG
#         # print(f"    🔍 Compétences stagiaire: {list(stagiaire_comp_clean)[:3]}...")
#         # print(f"    🔍 Compétences offre: {offre_comp_list}")
        
#         # Calcul des matches
#         total_matches = 0
#         matched_details = []
        
#         for offre_comp in offre_comp_list:
#             offre_comp_clean = offre_comp.lower().strip()
            
#             # Match exact
#             if offre_comp_clean in stagiaire_comp_clean:
#                 total_matches += 3
#                 matched_details.append(f"{offre_comp_clean} (exact)")
#                 continue
                
#             # Match partiel
#             found_partial = False
#             for stagiaire_comp in stagiaire_comp_clean:
#                 if (len(offre_comp_clean) > 3 and offre_comp_clean in stagiaire_comp) or \
#                    (len(stagiaire_comp) > 3 and stagiaire_comp in offre_comp_clean):
#                     total_matches += 2
#                     matched_details.append(f"{stagiaire_comp} ≈ {offre_comp_clean}")
#                     found_partial = True
#                     break
            
#             if found_partial:
#                 continue
                
#             # Match de mots-clés
#             for stagiaire_comp in stagiaire_comp_clean:
#                 offre_words = set(offre_comp_clean.split())
#                 stagiaire_words = set(stagiaire_comp.split())
#                 if offre_words & stagiaire_words:  # Intersection
#                     total_matches += 1
#                     matched_details.append(f"{stagiaire_comp} ~ {offre_comp_clean}")
#                     break
        
#         # Score sur 100
#         max_possible = len(offre_comp_list) * 3
#         score = min((total_matches / max_possible) * 100, 100) if max_possible > 0 else 0
        
#         # Bonus si beaucoup de compétences du stagiaire
#         if len(stagiaire_comp_clean) > 10:
#             score += 10
        
#         final_score = max(score, 30.0)  # Minimum 30%
        
#         # DEBUG
#         # print(f"    📊 Matches: {total_matches}/{max_possible} = {final_score:.1f}%")
#         # if matched_details:
#         #     print(f"    ✅ Détails: {matched_details[:2]}")
        
#         return final_score

#     @classmethod
#     def _calculate_secteur_score_improved(cls, stagiaire_specialite: str, offre_secteur: str) -> float:
#         """Calcul amélioré du score de secteur."""
#         if not stagiaire_specialite or not offre_secteur:
#             return 50.0
        
#         specialite_clean = stagiaire_specialite.lower().strip()
#         secteur_clean = offre_secteur.lower().strip()
        
#         # Match exact
#         if specialite_clean == secteur_clean:
#             return 100.0
        
#         # Match partiel
#         if specialite_clean in secteur_clean or secteur_clean in specialite_clean:
#             return 85.0
        
#         # Correspondances par domaines avec scores spécifiques
#         domain_mappings = {
#             'informatique': ['technologie', 'développement', 'logiciel', 'numérique', 'digital', 'web', 'système', 'it'],
#             'commerce': ['business', 'vente', 'marketing', 'commercial'],
#             'finance': ['banque', 'investissement', 'comptabilité', 'gestion'],
#             'marketing': ['communication', 'digital', 'réseaux sociaux', 'publicité'],
#             'design': ['créatif', 'graphisme', 'ux', 'ui', 'visuel']
#         }
        
#         # Vérifier les mappings de domaines
#         for domain, keywords in domain_mappings.items():
#             if domain in specialite_clean:
#                 if any(keyword in secteur_clean for keyword in keywords):
#                     return 75.0
        
#         # Recherche de mots-clés communs
#         specialite_words = set(specialite_clean.split())
#         secteur_words = set(secteur_clean.split())
#         common_words = specialite_words & secteur_words
        
#         if common_words:
#             return 60.0
        
#         return 40.0  # Score par défaut plus généreux

#     @classmethod
#     def _calculate_experience_score_simple(cls, niveau_etudes: str) -> float:
#         """Score d'expérience simplifié."""
#         if not niveau_etudes:
#             return 60.0
        
#         niveau_clean = niveau_etudes.lower()
        
#         if 'bac+5' in niveau_clean or 'master' in niveau_clean or 'ingénieur' in niveau_clean:
#             return 85.0
#         elif 'bac+3' in niveau_clean or 'licence' in niveau_clean:
#             return 75.0
#         elif 'bac+2' in niveau_clean or 'dut' in niveau_clean or 'bts' in niveau_clean:
#             return 70.0
#         else:
#             return 65.0

#     @classmethod
#     def _calculate_location_score_improved(cls, stagiaire_ville: str, offre_localisation: str) -> float:
#         """Score de localisation amélioré."""
#         if not stagiaire_ville or not offre_localisation:
#             return 60.0  # Score neutre plus élevé
        
#         ville_clean = stagiaire_ville.lower().strip()
#         localisation_clean = offre_localisation.lower().strip()
        
#         # Match exact
#         if ville_clean == localisation_clean or ville_clean in localisation_clean:
#             return 100.0
        
#         # Télétravail/Remote
#         if any(word in localisation_clean for word in ['remote', 'télétravail', 'distance', 'en ligne']):
#             return 95.0
        
#         # Villes principales du Maroc - distances acceptables
#         morocco_cities = {
#             'casablanca': ['rabat', 'mohammedia', 'el jadida'],
#             'rabat': ['casablanca', 'salé', 'kénitra'],
#             'marrakech': ['casablanca', 'agadir'],
#             'fès': ['meknès', 'rabat'],
#             'tanger': ['tétouan', 'rabat']
#         }
        
#         for main_city, nearby_cities in morocco_cities.items():
#             if ville_clean == main_city and any(city in localisation_clean for city in nearby_cities):
#                 return 75.0
#             if any(city == ville_clean for city in nearby_cities) and main_city in localisation_clean:
#                 return 75.0
        
#         return 50.0  # Score par défaut pour autres villes

#     @classmethod
#     def _build_recommendation_dict(cls, offre: Offre, scores: Dict[str, float]) -> Dict:
#         """Construire le dictionnaire de recommandation."""
        
#         # Générer les raisons
#         reasons = []
#         if scores['competence'] >= 70:
#             reasons.append("Excellente correspondance des compétences")
#         elif scores['competence'] >= 50:
#             reasons.append("Bonne correspondance des compétences")
        
#         if scores['secteur'] >= 80:
#             reasons.append("Secteur parfaitement adapté")
#         elif scores['secteur'] >= 60:
#             reasons.append("Secteur compatible")
        
#         if scores['location'] >= 90:
#             reasons.append("Localisation idéale")
#         elif scores['location'] >= 70:
#             reasons.append("Localisation accessible")
        
#         if not reasons:
#             reasons.append("Opportunité intéressante à explorer")
        
#         return {
#             "offre_id": offre.id,
#             "titre": offre.titre,
#             "entreprise_nom": offre.entreprise.raison_social if offre.entreprise else "N/A",
#             "secteur": offre.secteur,
#             "localisation": offre.localisation,
#             "type_stage": offre.type_stage,
#             "date_debut": offre.date_debut.isoformat() if offre.date_debut else None,
#             "date_fin": offre.date_fin.isoformat() if offre.date_fin else None,
#             "description": offre.description[:200] + "..." if offre.description and len(offre.description) > 200 else offre.description,
#             "match_score": scores['overall'],
#             "competence_match": scores['competence'],
#             "secteur_match": scores['secteur'], 
#             "experience_match": scores['experience'],
#             "location_match": scores['location'],
#             "recommendation_reasons": reasons,
#             "created_at": offre.created_at.isoformat() if offre.created_at else None
#         }

#     # ============================================================================
#     # MÉTHODES SUPPLÉMENTAIRES (Anciennes méthodes pour compatibilité)
#     # ============================================================================

#     @classmethod
#     def get_similar_profiles_recommendations(cls, db: Session, stagiaire_id: int, limit: int = 5) -> List[Dict]:
#         """Recommandations basées sur des profils similaires (collaborative filtering simple)."""
        
#         # Récupérer le stagiaire actuel
#         stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
#         if not stagiaire:
#             return []
        
#         # Trouver des stagiaires avec des profils similaires
#         stagiaires_similaires = db.query(Stagiaire).filter(
#             Stagiaire.id != stagiaire_id,
#             Stagiaire.specialite == stagiaire.specialite,
#             Stagiaire.niveau_etudes == stagiaire.niveau_etudes
#         ).limit(10).all()
        
#         if not stagiaires_similaires:
#             return []
        
#         # Récupérer les offres auxquelles ces stagiaires ont candidaté avec succès
#         from app.models.candidature import StatusCandidature
        
#         try:
#             offres_similaires = db.query(Offre).join(Candidature).filter(
#                 Candidature.stagiaire_id.in_([s.id for s in stagiaires_similaires]),
#                 Candidature.status == StatusCandidature.ACCEPTEE,
#                 Offre.est_active == True,
#                 Offre.date_fin >= datetime.now().date()
#             ).distinct().limit(limit).all()
            
#             recommendations = []
#             for offre in offres_similaires:
#                 recommendations.append({
#                     "offre_id": offre.id,
#                     "titre": offre.titre,
#                     "entreprise_nom": offre.entreprise.raison_social if offre.entreprise else "N/A",
#                     "secteur": offre.secteur,
#                     "reason": "Recommandé par des profils similaires"
#                 })
            
#             return recommendations
            
#         except Exception as e:
#             print(f"❌ Erreur profils similaires: {e}")
#             return []

#     # ============================================================================
#     # MÉTHODES DE TEST ET DEBUG
#     # ============================================================================

#     @classmethod
#     def test_single_match(cls, db: Session, stagiaire_id: int, offre_id: int) -> Dict:
#         """Tester le matching pour une offre spécifique - POUR DEBUG."""
        
#         stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
#         offre = db.query(Offre).options(joinedload(Offre.entreprise)).filter(Offre.id == offre_id).first()
        
#         if not stagiaire or not offre:
#             return {"error": "Stagiaire ou offre non trouvé"}
        
#         stagiaire_competences = stagiaire.get_all_competences()
#         scores = cls._calculate_all_scores(stagiaire, offre, stagiaire_competences)
        
#         return {
#             "stagiaire": {
#                 "id": stagiaire.id,
#                 "specialite": stagiaire.specialite,
#                 "niveau_etudes": stagiaire.niveau_etudes,
#                 "ville": stagiaire.ville,
#                 "competences": stagiaire_competences[:10]  # Premières 10
#             },
#             "offre": {
#                 "id": offre.id,
#                 "titre": offre.titre,
#                 "secteur": offre.secteur,
#                 "localisation": offre.localisation,
#                 "competences_requises": offre.competences_requises
#             },
#             "scores_detailles": scores,
#             "recommendation": cls._build_recommendation_dict(offre, scores)
#         }