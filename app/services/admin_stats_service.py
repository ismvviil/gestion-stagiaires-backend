from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List
from datetime import datetime, timedelta

from app.models.utilisateur import Utilisateur
from app.models.stagiaire import Stagiaire
from app.models.recruteur import Recruteur
from app.models.responsable_rh import ResponsableRH
from app.models.admin import Admin
from app.models.entreprise import Entreprise
from app.models.offre import Offre
from app.models.candidature import Candidature, StatusCandidature
from app.models.stage import Stage
from app.models.evaluation import Evaluation , Certificat
from app.schemas.admin_stats import *

class AdminStatsService:
    """Service pour calculer les statistiques admin."""
    
    @staticmethod
    def obtenir_statistiques_globales(db: Session) -> StatistiquesGlobales:
        """Calcule les statistiques globales de la plateforme."""
        
        # Compter les utilisateurs par type
        nombre_stagiaires = db.query(Stagiaire).count()
        nombre_recruteurs = db.query(Recruteur).count()
        nombre_rh = db.query(ResponsableRH).count()
        nombre_admins = db.query(Admin).count()
        nombre_total = nombre_stagiaires + nombre_recruteurs + nombre_rh + nombre_admins
        
        # Entreprises
        nombre_entreprises = db.query(Entreprise).count()
        
        # Calculer entreprises actives (qui ont au moins une offre dans les 6 derniers mois)
        six_mois_ago = datetime.now() - timedelta(days=180)
        entreprises_actives = db.query(Entreprise.id).join(Offre).filter(
            Offre.created_at >= six_mois_ago
        ).distinct().count()
        
        # Offres
        nombre_offres_total = db.query(Offre).count()
        nombre_offres_actives = db.query(Offre).filter(Offre.est_active == True).count()
        
        # Candidatures
        nombre_candidatures_total = db.query(Candidature).count()
        nombre_candidatures_acceptees = db.query(Candidature).filter(
            Candidature.status == StatusCandidature.ACCEPTEE
        ).count()
        
        # Stages
        nombre_stages_total = db.query(Stage).count()
        nombre_stages_termines = db.query(Stage).filter(
            Stage.status == "termine"
        ).count()
        
        # Évaluations et certificats
        nombre_evaluations_total = db.query(Evaluation).count()
        nombre_certificats_generes = db.query(Certificat).count()
        
        # Calculs des taux
        taux_acceptation = None
        if nombre_candidatures_total > 0:
            taux_acceptation = round((nombre_candidatures_acceptees / nombre_candidatures_total) * 100, 2)
        
        taux_completion = None
        if nombre_stages_total > 0:
            taux_completion = round((nombre_stages_termines / nombre_stages_total) * 100, 2)
        
        # Note moyenne globale
        note_moyenne = db.query(func.avg(Evaluation.note_globale)).filter(
            Evaluation.note_globale.isnot(None)
        ).scalar()
        note_moyenne = round(note_moyenne, 2) if note_moyenne else None
        
        return StatistiquesGlobales(
            nombre_total_utilisateurs=nombre_total,
            nombre_stagiaires=nombre_stagiaires,
            nombre_recruteurs=nombre_recruteurs,
            nombre_rh=nombre_rh,
            nombre_admins=nombre_admins,
            nombre_entreprises=nombre_entreprises,
            entreprises_actives=entreprises_actives,
            nombre_offres_total=nombre_offres_total,
            nombre_offres_actives=nombre_offres_actives,
            nombre_candidatures_total=nombre_candidatures_total,
            nombre_candidatures_acceptees=nombre_candidatures_acceptees,
            nombre_stages_total=nombre_stages_total,
            nombre_stages_termines=nombre_stages_termines,
            nombre_evaluations_total=nombre_evaluations_total,
            nombre_certificats_generes=nombre_certificats_generes,
            taux_acceptation_candidatures=taux_acceptation,
            taux_completion_stages=taux_completion,
            note_moyenne_globale=note_moyenne
        )
    
    @staticmethod
    def obtenir_evolution_temporelle(db: Session, mois_nombre: int = 12) -> List[StatistiquesTemporelles]:
        """Obtient l'évolution des métriques sur les derniers mois."""
        
        stats = []
        for i in range(mois_nombre):
            # Calculer le premier et dernier jour du mois
            date_fin = datetime.now().replace(day=1) - timedelta(days=i*30)
            date_debut = date_fin.replace(day=1)
            date_fin_mois = (date_debut + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Compter les nouvelles inscriptions
            nouvelles_inscriptions = db.query(Utilisateur).filter(
                Utilisateur.created_at >= date_debut,
                Utilisateur.created_at <= date_fin_mois
            ).count()
            
            # Nouvelles offres
            nouvelles_offres = db.query(Offre).filter(
                Offre.created_at >= date_debut,
                Offre.created_at <= date_fin_mois
            ).count()
            
            # Nouvelles candidatures
            nouvelles_candidatures = db.query(Candidature).filter(
                Candidature.created_at >= date_debut,
                Candidature.created_at <= date_fin_mois
            ).count()
            
            # Stages commencés (date_debut_reel dans ce mois)
            stages_commences = db.query(Stage).filter(
                Stage.date_debut_reel >= date_debut,
                Stage.date_debut_reel <= date_fin_mois
            ).count()
            
            # Stages terminés (date_fin_reel dans ce mois)
            stages_termines = db.query(Stage).filter(
                Stage.date_fin_reel >= date_debut,
                Stage.date_fin_reel <= date_fin_mois
            ).count()
            
            stats.append(StatistiquesTemporelles(
                mois=date_debut.strftime("%Y-%m"),
                nouvelles_inscriptions=nouvelles_inscriptions,
                nouvelles_offres=nouvelles_offres,
                nouvelles_candidatures=nouvelles_candidatures,
                stages_commences=stages_commences,
                stages_termines=stages_termines
            ))
        
        return list(reversed(stats))  # Du plus ancien au plus récent
    
    @staticmethod
    def obtenir_stats_entreprises(db: Session, limit: int = 20) -> List[StatistiquesEntreprises]:
        """Obtient les statistiques des principales entreprises."""
        
        # Requête complexe pour obtenir toutes les stats en une fois
        entreprises_stats = db.query(
            Entreprise.id,
            Entreprise.raison_social,
            Entreprise.secteur_activite,
            func.count(Recruteur.id).label('nombre_recruteurs'),
            func.count(Offre.id).label('nombre_offres'),
            func.count(Candidature.id).label('nombre_candidatures'),
            func.count(Stage.id).label('nombre_stages'),
            func.avg(Evaluation.note_globale).label('note_moyenne')
        ).outerjoin(Recruteur, Entreprise.id == Recruteur.entreprise_id)\
         .outerjoin(Offre, Entreprise.id == Offre.entreprise_id)\
         .outerjoin(Candidature, Offre.id == Candidature.offre_id)\
         .outerjoin(Stage, Entreprise.id == Stage.entreprise_id)\
         .outerjoin(Evaluation, Stage.id == Evaluation.stage_id)\
         .group_by(Entreprise.id, Entreprise.raison_social, Entreprise.secteur_activite)\
         .order_by(func.count(Stage.id).desc())\
         .limit(limit).all()
        
        return [
            StatistiquesEntreprises(
                entreprise_id=stat.id,
                nom_entreprise=stat.raison_social,
                secteur=stat.secteur_activite or "Non spécifié",
                nombre_recruteurs=stat.nombre_recruteurs or 0,
                nombre_offres=stat.nombre_offres or 0,
                nombre_candidatures_recues=stat.nombre_candidatures or 0,
                nombre_stages_encadres=stat.nombre_stages or 0,
                note_moyenne_evaluations=round(stat.note_moyenne, 2) if stat.note_moyenne else None
            )
            for stat in entreprises_stats
        ]
    
    @staticmethod
    def obtenir_stats_secteurs(db: Session) -> List[StatistiquesSecteurs]:
        """Obtient les statistiques par secteur d'activité."""
        
        secteurs_stats = db.query(
            Entreprise.secteur_activite,
            func.count(Entreprise.id).label('nombre_entreprises'),
            func.count(Offre.id).label('nombre_offres'),
            func.count(Stage.id).label('nombre_stages'),
            func.avg(Evaluation.note_globale).label('note_moyenne')
        ).outerjoin(Offre, Entreprise.id == Offre.entreprise_id)\
         .outerjoin(Stage, Entreprise.id == Stage.entreprise_id)\
         .outerjoin(Evaluation, Stage.id == Evaluation.stage_id)\
         .group_by(Entreprise.secteur_activite)\
         .order_by(func.count(Entreprise.id).desc()).all()
        
        return [
            StatistiquesSecteurs(
                secteur=stat.secteur_activite or "Non spécifié",
                nombre_entreprises=stat.nombre_entreprises or 0,
                nombre_offres=stat.nombre_offres or 0,
                nombre_stages=stat.nombre_stages or 0,
                note_moyenne=round(stat.note_moyenne, 2) if stat.note_moyenne else None
            )
            for stat in secteurs_stats
        ]
    
    @staticmethod
    def obtenir_utilisateurs_details(
        db: Session, 
        type_filtre: str = None, 
        actif_filtre: bool = None,
        skip: int = 0, 
        limit: int = 50
    ) -> List[UtilisateurDetaille]:
        """Obtient la liste détaillée des utilisateurs."""
        
        query = db.query(Utilisateur)
        
        if type_filtre:
            query = query.filter(Utilisateur.type == type_filtre)
        
        if actif_filtre is not None:
            query = query.filter(Utilisateur.actif == actif_filtre)
        
        utilisateurs = query.offset(skip).limit(limit).all()
        
        result = []
        for user in utilisateurs:
            user_detail = UtilisateurDetaille(
                id=user.id,
                email=user.email,
                nom=user.nom,
                prenom=user.prenom,
                type=user.type,
                actif=user.actif,
                created_at=user.created_at
            )
            
            # Ajouter des informations spécifiques selon le type
            if user.type == "stagiaire":
                # Compter les candidatures
                nb_candidatures = db.query(Candidature).filter(
                    Candidature.stagiaire_id == user.id
                ).count()
                user_detail.nombre_candidatures = nb_candidatures
                
            elif user.type in ["recruteur", "responsable_rh"]:
                # Obtenir le nom de l'entreprise et compter les offres
                if hasattr(user, 'entreprise_id') and user.entreprise_id:
                    entreprise = db.query(Entreprise).filter(
                        Entreprise.id == user.entreprise_id
                    ).first()
                    if entreprise:
                        user_detail.entreprise_nom = entreprise.raison_social
                
                if user.type == "recruteur":
                    nb_offres = db.query(Offre).filter(
                        Offre.recruteur_id == user.id
                    ).count()
                    user_detail.nombre_offres = nb_offres
            
            result.append(user_detail)
        
        return result