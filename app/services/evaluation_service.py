# app/services/evaluation_service.py
import uuid
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.evaluation import (
    CritereEvaluation, Evaluation, DetailEvaluation, 
    Certificat, StatutEvaluation, StatutCertificat
)

from app.models.stage import Stage
from app.models.candidature import Candidature
from app.models.utilisateur import Utilisateur
from app.models.entreprise import Entreprise
from app.schemas.evaluation import (
    EvaluationCreate, CertificatGeneration, StatistiquesEvaluation
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from typing import Dict, Any, Optional

# class CodeUniqueService:
#     """Service pour générer des codes uniques."""
    
#     @staticmethod
#     def generer_code_certificat(db: Session, annee: int = None) -> str:
#         """Génère un code unique pour un certificat."""
#         if annee is None:
#             annee = datetime.now().year
        
#         while True:
#             # Format: CERT-YYYY-XXXXXXXX (8 caractères aléatoires)
#             code_aleatoire = str(uuid.uuid4()).replace('-', '').upper()[:8]
#             code_unique = f"CERT-{annee}-{code_aleatoire}"
            
#             # Vérifier l'unicité
#             existe = db.query(Certificat).filter(
#                 Certificat.code_unique == code_unique
#             ).first()
            
#             if not existe:
#                 return code_unique
            
# class QRCodeService:
#     """Service pour générer des QR codes."""
    
#     @staticmethod
#     def generer_qr_code(
#         code_unique: str, 
#         base_url: str = "http://localhost:8000"
#     ) -> str:
#         """Génère un QR code pour un certificat et retourne les données base64."""
        
#         # URL de vérification
#         verification_url = f"{base_url}/api/certificats/verify/{code_unique}"
        
#         # Créer le QR code
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4,
#         )
#         qr.add_data(verification_url)
#         qr.make(fit=True)
        
#         # Créer l'image
#         img = qr.make_image(fill_color="black", back_color="white")
        
#         # Convertir en base64
#         buffer = BytesIO()
#         img.save(buffer, format='PNG')
#         buffer.seek(0)
        
#         # Encoder en base64
#         qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
#         return qr_base64
    
#     @staticmethod
#     def generer_qr_code_donnees(donnees: Dict[str, Any]) -> str:
#         """Génère un QR code avec des données personnalisées."""
#         import json
        
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_M,
#             box_size=10,
#             border=4,
#         )
        
#         # Convertir les données en JSON
#         qr.add_data(json.dumps(donnees))
#         qr.make(fit=True)
        
#         img = qr.make_image(fill_color="black", back_color="white")
        
#         buffer = BytesIO()
#         img.save(buffer, format='PNG')
#         buffer.seek(0)
        
#         return base64.b64encode(buffer.getvalue()).decode()
    

# class EvaluationService:
#     """Service pour gérer les évaluations."""
    
#     @staticmethod
#     def creer_evaluation(
#         db: Session, 
#         evaluation_data: EvaluationCreate, 
#         evaluateur_id: int
#     ) -> Evaluation:
#         """Crée une nouvelle évaluation."""
        
#         # Vérifier que le stage existe et est terminé
#         stage = db.query(Stage).filter(Stage.id == evaluation_data.stage_id).first()
#         if not stage:
#             raise ValueError("Stage non trouvé")
        
#         if stage.status.value != "termine":
#             raise ValueError("Le stage doit être terminé pour être évalué")
        
#         # Vérifier qu'il n'y a pas déjà d'évaluation
#         evaluation_existante = db.query(Evaluation).filter(
#             Evaluation.stage_id == evaluation_data.stage_id
#         ).first()
#         if evaluation_existante:
#             raise ValueError("Ce stage a déjà été évalué")
        
#         # Créer l'évaluation
#         evaluation = Evaluation(
#             **evaluation_data.dict(exclude={'details'}),
#             evaluateur_id=evaluateur_id,
#             statut=StatutEvaluation.BROUILLON
#         )
#         db.add(evaluation)
#         db.flush()  # Pour obtenir l'ID
        
#         # Ajouter les détails
#         for detail_data in evaluation_data.details:
#             detail = DetailEvaluation(
#                 **detail_data.dict(),
#                 evaluation_id=evaluation.id
#             )
#             db.add(detail)
        
#         # 🔧 FIX CRITIQUE : Flush pour charger les relations
#         db.flush()
        
#         # 🔧 FIX CRITIQUE : Rafraîchir l'objet pour charger les relations
#         db.refresh(evaluation)
        
#         # 🔧 FIX CRITIQUE : Calculer la note globale
#         note_calculee = EvaluationService._calculer_note_globale_service(db, evaluation.id)
#         evaluation.note_globale = note_calculee
        
#         db.commit()
#         db.refresh(evaluation)
#         return evaluation
    
#     @staticmethod
#     def valider_evaluation(db: Session, evaluation_id: int) -> Evaluation:
#         """Valide une évaluation."""
#         evaluation = db.query(Evaluation).filter(
#             Evaluation.id == evaluation_id
#         ).first()
        
#         if not evaluation:
#             raise ValueError("Évaluation non trouvée")
        
#         if evaluation.statut == StatutEvaluation.VALIDEE:
#             raise ValueError("Évaluation déjà validée")
        
#         evaluation.valider_evaluation()
#         db.commit()
#         db.refresh(evaluation)
#         return evaluation
    
#     @staticmethod
#     def obtenir_criteres_evaluation(
#         db: Session, 
#         entreprise_id: Optional[int] = None
#     ) -> List[CritereEvaluation]:
#         """Obtient les critères d'évaluation disponibles."""
#         query = db.query(CritereEvaluation).filter(
#             CritereEvaluation.actif == True
#         )
        
#         # Critères globaux + critères de l'entreprise
#         if entreprise_id:
#             query = query.filter(
#                 (CritereEvaluation.est_global == True) |
#                 (CritereEvaluation.entreprise_id == entreprise_id)
#             )
#         else:
#             query = query.filter(CritereEvaluation.est_global == True)
        
#         return query.all()
    
#     @staticmethod
#     def calculer_statistiques_evaluation(
#         db: Session, 
#         entreprise_id: Optional[int] = None
#     ) -> StatistiquesEvaluation:
#         """Calcule les statistiques d'évaluation."""
#         query = db.query(Evaluation)
        
#         if entreprise_id:
#             query = query.join(Stage).filter(Stage.entreprise_id == entreprise_id)
        
#         evaluations = query.all()
        
#         nombre_total = len(evaluations)
#         nombre_validees = len([e for e in evaluations if e.statut == StatutEvaluation.VALIDEE])
        
#         # Note moyenne
#         notes = [e.note_globale for e in evaluations if e.note_globale is not None]
#         note_moyenne = sum(notes) / len(notes) if notes else None
        
#         # Répartition des mentions
#         mentions = {}
#         for evaluation in evaluations:
#             if evaluation.note_globale:
#                 mention = CertificatService.calculer_mention(evaluation.note_globale)
#                 mentions[mention] = mentions.get(mention, 0) + 1
        
#         # Taux de recommandation d'embauche
#         recommandations = [e for e in evaluations if e.recommande_embauche is not None]
#         taux_recommandation = None
#         if recommandations:
#             nombre_recommandations = len([e for e in recommandations if e.recommande_embauche])
#             taux_recommandation = (nombre_recommandations / len(recommandations)) * 100
        
#         return StatistiquesEvaluation(
#             nombre_evaluations_total=nombre_total,
#             nombre_evaluations_validees=nombre_validees,
#             note_moyenne=note_moyenne,
#             repartition_mentions=mentions,
#             taux_recommandation_embauche=taux_recommandation
#         )
    
# class CertificatService:
#     """Service pour gérer les certificats."""
    
#     @staticmethod
#     def generer_certificat(
#         db: Session, 
#         evaluation_id: int, 
#         generateur_id: int,
#         base_url: str = "http://localhost:8000"
#     ) -> Certificat:
#         """Génère un certificat à partir d'une évaluation."""
        
#          # Récupérer l'évaluation avec toutes les relations
#         evaluation = db.query(Evaluation).filter(
#             Evaluation.id == evaluation_id
#         ).first()
        
#         if not evaluation:
#             raise ValueError("Évaluation non trouvée")
        
#         if evaluation.statut != StatutEvaluation.VALIDEE:
#             raise ValueError("L'évaluation doit être validée pour générer un certificat")
        
#         # Vérifier qu'il n'y a pas déjà de certificat
#         certificat_existant = db.query(Certificat).filter(
#             Certificat.evaluation_id == evaluation_id
#         ).first()
#         if certificat_existant:
#             raise ValueError("Un certificat a déjà été généré pour cette évaluation")
        
#         # Récupérer les données nécessaires
#         stage = evaluation.stage
#         candidature = stage.candidature
#         stagiaire = candidature.stagiaire
#         entreprise = stage.entreprise
#         generateur = db.query(Utilisateur).filter(Utilisateur.id == generateur_id).first()
        
#         # Calculer la durée du stage
#         duree_jours = (stage.date_fin - stage.date_debut).days
        
#         # Générer le code unique
#         code_unique = CodeUniqueService.generer_code_certificat(db)
        
#         # Générer le QR code
#         qr_code_data = QRCodeService.generer_qr_code(code_unique, base_url)
        
#         # Créer le certificat
#         certificat = Certificat(
#             code_unique=code_unique,
#             titre_stage=candidature.offre.titre,
#             date_debut_stage=stage.date_debut,
#             date_fin_stage=stage.date_fin,
#             duree_stage_jours=duree_jours,
#             note_finale=evaluation.note_globale,
#             mention=CertificatService.calculer_mention(evaluation.note_globale),
#             nom_stagiaire=stagiaire.nom,
#             prenom_stagiaire=stagiaire.prenom,
#             nom_entreprise=entreprise.raison_social,
#             secteur_entreprise=entreprise.secteur_activite,
#             nom_evaluateur=generateur.nom,
#             prenom_evaluateur=generateur.prenom,
#             poste_evaluateur=getattr(generateur, 'poste', 'Évaluateur'),
#             qr_code_data=qr_code_data,
#             evaluation_id=evaluation_id,
#             candidature_id=candidature.id,
#             stage_id=stage.id,
#             entreprise_id=entreprise.id,
#             generateur_id=generateur_id,
#             statut=StatutCertificat.GENERE
#         )
        
#         db.add(certificat)
#         db.commit()
#         db.refresh(certificat)
#         return certificat
    
#     @staticmethod
#     def calculer_mention(note: float) -> str:
#         """Calcule la mention basée sur la note."""
#         if note >= 9:
#             return "Excellent"
#         elif note >= 8:
#             return "Très Bien"
#         elif note >= 7:
#             return "Bien"
#         elif note >= 6:
#             return "Assez Bien"
#         elif note >= 5:
#             return "Passable"
#         else:
#             return "Insuffisant"
    
#     @staticmethod
#     def verifier_certificat(db: Session, code_unique: str) -> Optional[Certificat]:
#         """Vérifie l'authenticité d'un certificat."""
#         certificat = db.query(Certificat).filter(
#             Certificat.code_unique == code_unique
#         ).first()
        
#         if certificat:
#             # Incrémenter le compteur de vérifications
#             certificat.incrementer_verifications()
#             db.commit()
        
#         return certificat
    
#     @staticmethod
#     def marquer_comme_telecharge(db: Session, certificat_id: int):
#         """Marque un certificat comme téléchargé."""
#         certificat = db.query(Certificat).filter(Certificat.id == certificat_id).first()
#         if certificat:
#             certificat.statut = StatutCertificat.TELECHARGE
#             certificat.date_dernier_telechargement = func.now()
#             db.commit()

# class VerificationService:
#     """Service pour la vérification des certificats."""
    
#     @staticmethod
#     def verifier_par_qr_code(db: Session, code_unique: str) -> Dict[str, Any]:
#         """Vérifie un certificat via son code QR."""
#         certificat = CertificatService.verifier_certificat(db, code_unique)
        
#         if not certificat:
#             return {
#                 "valide": False,
#                 "message": "Certificat non trouvé ou invalide",
#                 "certificat": None
#             }
        
#         # Vérifications supplémentaires
#         if certificat.statut == StatutCertificat.GENERE:
#             statut_message = "Certificat valide"
#         elif certificat.statut == StatutCertificat.TELECHARGE:
#             statut_message = "Certificat valide et téléchargé"
#         else:
#             statut_message = "Certificat valide"
        
#         return {
#             "valide": True,
#             "message": statut_message,
#             "certificat": certificat,
#             "verification_numero": certificat.nombre_verifications
#         }
    
#     @staticmethod
#     def obtenir_historique_verifications(
#         db: Session, 
#         certificat_id: int
#     ) -> Dict[str, Any]:
#         """Obtient l'historique des vérifications d'un certificat."""
#         certificat = db.query(Certificat).filter(Certificat.id == certificat_id).first()
        
#         if not certificat:
#             return {"erreur": "Certificat non trouvé"}
        
#         return {
#             "code_unique": certificat.code_unique,
#             "nombre_verifications": certificat.nombre_verifications,
#             "date_generation": certificat.date_generation,
#             "date_dernier_telechargement": certificat.date_dernier_telechargement,
#             "statut": certificat.statut.value
#         }


# app/services/evaluation_service.py - VERSION COMPLÈTE CORRIGÉE

from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import base64
import qrcode
from io import BytesIO

from app.models.evaluation import *
from app.models.stage import Stage
from app.models.utilisateur import Utilisateur
from app.schemas.evaluation import EvaluationCreate, StatistiquesEvaluation

class CodeUniqueService:
    """Service pour générer des codes uniques."""
    
    @staticmethod
    def generer_code_certificat(db: Session, annee: int = None) -> str:
        """Génère un code unique pour un certificat."""
        if annee is None:
            annee = datetime.now().year
        
        while True:
            code_aleatoire = str(uuid.uuid4()).replace('-', '').upper()[:8]
            code_unique = f"CERT-{annee}-{code_aleatoire}"
            
            existe = db.query(Certificat).filter(
                Certificat.code_unique == code_unique
            ).first()
            
            if not existe:
                return code_unique

class QRCodeService:
    """Service pour générer des QR codes."""
    
    @staticmethod
    def generer_qr_code(
        code_unique: str, 
        base_url: str = "http://localhost:8000"
    ) -> str:
        """Génère un QR code pour un certificat et retourne les données base64."""
        
        verification_url = f"{base_url}/api/evaluations/certificats/verify/{code_unique}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        return qr_base64

class EvaluationService:
    """Service pour gérer les évaluations."""
    
    @staticmethod
    def creer_evaluation(
        db: Session, 
        evaluation_data: EvaluationCreate, 
        evaluateur_id: int
    ) -> Evaluation:
        """Crée une nouvelle évaluation avec calcul automatique de la note."""
        
        # Vérifier que le stage existe
        stage = db.query(Stage).filter(Stage.id == evaluation_data.stage_id).first()
        if not stage:
            raise ValueError("Stage non trouvé")
        
        if stage.status != "termine":
            raise ValueError("Le stage doit être terminé pour être évalué")
    
        # Vérifier qu'il n'y a pas déjà d'évaluation
        evaluation_existante = db.query(Evaluation).filter(
            Evaluation.stage_id == evaluation_data.stage_id
        ).first()
        if evaluation_existante:
            # raise ValueError("Ce stage a déjà été évalué")
            raise ValueError(f"Ce stage a déjà été évalué (Évaluation #{evaluation_existante.id})")
        
        # Créer l'évaluation principale
        evaluation = Evaluation(
            stage_id=evaluation_data.stage_id,
            evaluateur_id=evaluateur_id,
            commentaire_general=evaluation_data.commentaire_general,
            points_forts=evaluation_data.points_forts,
            points_amelioration=evaluation_data.points_amelioration,
            recommandations=evaluation_data.recommandations,
            recommande_embauche=evaluation_data.recommande_embauche,
            statut=StatutEvaluation.BROUILLON
        )
        
        db.add(evaluation)
        db.flush()  # Pour obtenir l'ID
        
        # Ajouter les détails d'évaluation
        for detail_data in evaluation_data.details:
            detail = DetailEvaluation(
                evaluation_id=evaluation.id,
                critere_id=detail_data.critere_id,
                note=detail_data.note,
                commentaire=detail_data.commentaire
            )
            db.add(detail)
        
        # 🔧 SOLUTION : Calculer immédiatement la note globale
        db.flush()  # S'assurer que les détails sont en base
        
        # 🎯 CALCUL DIRECT DE LA NOTE GLOBALE
        note_globale = EvaluationService._calculer_note_globale_service(db, evaluation.id)
        evaluation.note_globale = note_globale
        
        print(f"🔢 Note globale calculée: {note_globale}")
        
        db.commit()
        db.refresh(evaluation)
        return evaluation
    
    @staticmethod
    def _calculer_note_globale_service(db: Session, evaluation_id: int) -> Optional[float]:
        """🎯 MÉTHODE MANQUANTE : Calcule la note globale d'une évaluation."""
        
        # Récupérer tous les détails avec leurs critères
        details = db.query(DetailEvaluation).join(CritereEvaluation).filter(
            DetailEvaluation.evaluation_id == evaluation_id,
            CritereEvaluation.actif == True
        ).all()
        
        if not details:
            print("❌ Aucun détail trouvé pour l'évaluation")
            return None
        
        print(f"📊 Calcul pour {len(details)} critères:")
        
        total_poids = 0
        note_ponderee = 0
        
        for detail in details:
            poids = detail.critere.poids
            note = detail.note
            contribution = note * poids
            
            total_poids += poids
            note_ponderee += contribution
            
            print(f"  - {detail.critere.nom}: note={note}, poids={poids}, contribution={contribution}")
        
        if total_poids == 0:
            print("❌ Total des poids = 0")
            return None
        
        note_finale = round(note_ponderee / total_poids, 2)
        print(f"🎯 Résultat: {note_ponderee} ÷ {total_poids} = {note_finale}")
        
        return note_finale
    
    @staticmethod
    def finaliser_evaluation(db: Session, evaluation_id: int) -> Evaluation:
        """Finalise une évaluation (BROUILLON → TERMINEE)."""
        
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise ValueError("Évaluation non trouvée")
        
        if evaluation.statut != StatutEvaluation.BROUILLON:
            raise ValueError("Seules les évaluations en brouillon peuvent être finalisées")
        
        # Recalculer la note si nécessaire
        if evaluation.note_globale is None:
            note_calculee = EvaluationService._calculer_note_globale_service(db, evaluation_id)
            evaluation.note_globale = note_calculee
        
        if not evaluation.details or evaluation.note_globale is None:
            raise ValueError("L'évaluation doit être complète avant finalisation")
        
        evaluation.statut = StatutEvaluation.TERMINEE
        
        db.commit()
        db.refresh(evaluation)
        return evaluation
    
    @staticmethod
    def valider_evaluation(db: Session, evaluation_id: int) -> Evaluation:
        """Valide une évaluation (TERMINEE → VALIDEE)."""
        
        evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if not evaluation:
            raise ValueError("Évaluation non trouvée")
        
        if evaluation.statut != StatutEvaluation.TERMINEE:
            raise ValueError("Seules les évaluations terminées peuvent être validées")
        
        evaluation.statut = StatutEvaluation.VALIDEE
        evaluation.date_validation = func.now()
        
        db.commit()
        db.refresh(evaluation)
        return evaluation
    
    @staticmethod
    def obtenir_criteres_evaluation(
        db: Session, 
        entreprise_id: Optional[int] = None
    ) -> List[CritereEvaluation]:
        """Obtient les critères d'évaluation disponibles."""
        
        query = db.query(CritereEvaluation).filter(CritereEvaluation.actif == True)
        
        if entreprise_id:
            query = query.filter(
                (CritereEvaluation.est_global == True) |
                (CritereEvaluation.entreprise_id == entreprise_id)
            )
        else:
            query = query.filter(CritereEvaluation.est_global == True)
        
        return query.all()
    

    @staticmethod
    def calculer_statistiques_recruteur(db: Session, recruteur_id: int) -> StatistiquesEvaluation:
        """Calculer les statistiques d'évaluation pour un recruteur spécifique."""
        
        # 🔧 Récupérer toutes les évaluations du recruteur
        evaluations = db.query(Evaluation)\
            .join(Stage)\
            .filter(Stage.recruteur_id == recruteur_id)\
            .all()
        
        if not evaluations:
            return StatistiquesEvaluation(
                nombre_evaluations_total=0,
                nombre_evaluations_validees=0,
                note_moyenne=None,
                repartition_mentions={},
                taux_recommandation_embauche=None
            )
        
        # Calculer les statistiques
        nombre_total = len(evaluations)
        
        # Évaluations validées
        evaluations_validees = [e for e in evaluations if e.statut == StatutEvaluation.VALIDEE]
        nombre_validees = len(evaluations_validees)
        
        # Note moyenne
        notes = [e.note_globale for e in evaluations if e.note_globale is not None]
        note_moyenne = sum(notes) / len(notes) if notes else None
        
        # Répartition des mentions
        def calculer_mention(note):
            if note >= 9:
                return "Excellent"
            elif note >= 8:
                return "Très Bien"
            elif note >= 7:
                return "Bien"
            elif note >= 6:
                return "Assez Bien"
            elif note >= 5:
                return "Passable"
            else:
                return "Insuffisant"
        
        repartition_mentions = {}
        for note in notes:
            mention = calculer_mention(note)
            repartition_mentions[mention] = repartition_mentions.get(mention, 0) + 1
        
        # Taux de recommandation d'embauche
        evaluations_avec_recommandation = [
            e for e in evaluations 
            if e.recommande_embauche is not None
        ]
        
        if evaluations_avec_recommandation:
            recommandations_positives = [
                e for e in evaluations_avec_recommandation 
                if e.recommande_embauche is True
            ]
            taux_recommandation = (len(recommandations_positives) / len(evaluations_avec_recommandation)) * 100
        else:
            taux_recommandation = None
        
        return StatistiquesEvaluation(
            nombre_evaluations_total=nombre_total,
            nombre_evaluations_validees=nombre_validees,
            note_moyenne=round(note_moyenne, 2) if note_moyenne else None,
            repartition_mentions=repartition_mentions,
            taux_recommandation_embauche=round(taux_recommandation, 1) if taux_recommandation else None
        )
    
    @staticmethod
    def calculer_statistiques_evaluation(
        db: Session, 
        entreprise_id: Optional[int] = None
    ) -> StatistiquesEvaluation:
        """Calcule les statistiques d'évaluation."""
        
        query = db.query(Evaluation)
        if entreprise_id:
            query = query.join(Stage).filter(Stage.entreprise_id == entreprise_id)
        
        evaluations = query.all()
        
        nombre_total = len(evaluations)
        nombre_validees = len([e for e in evaluations if e.statut == StatutEvaluation.VALIDEE])
        
        # Note moyenne
        notes = [e.note_globale for e in evaluations if e.note_globale is not None]
        note_moyenne = round(sum(notes) / len(notes), 2) if notes else None
        
        # Répartition des mentions
        mentions = {}
        for evaluation in evaluations:
            if evaluation.note_globale:
                mention = CertificatService.calculer_mention(evaluation.note_globale)
                mentions[mention] = mentions.get(mention, 0) + 1
        
        # Taux de recommandation
        recommandations = [e for e in evaluations if e.recommande_embauche is not None]
        taux_recommandation = None
        if recommandations:
            nombre_recommandations = len([e for e in recommandations if e.recommande_embauche])
            taux_recommandation = round((nombre_recommandations / len(recommandations)) * 100, 2)
        
        return StatistiquesEvaluation(
            nombre_evaluations_total=nombre_total,
            nombre_evaluations_validees=nombre_validees,
            note_moyenne=note_moyenne,
            repartition_mentions=mentions,
            taux_recommandation_embauche=taux_recommandation
        )




class CertificatService:
    """Service pour gérer les certificats."""
    
    @staticmethod
    def generer_certificat(
        db: Session, 
        evaluation_id: int, 
        generateur_id: int,
        base_url: str = "http://localhost:8000"
    ) -> Dict[str, Any]:
        """Génère un certificat à partir d'une évaluation validée."""
        
        # 🔧 Charger l'évaluation avec toutes les relations nécessaires
        evaluation = db.query(Evaluation).options(
            joinedload(Evaluation.stage).joinedload(Stage.stagiaire),
            joinedload(Evaluation.stage).joinedload(Stage.entreprise),
            joinedload(Evaluation.stage).joinedload(Stage.candidature).joinedload(Candidature.offre),
            joinedload(Evaluation.evaluateur)
        ).filter(Evaluation.id == evaluation_id).first()
        
        if not evaluation:
            raise ValueError("Évaluation non trouvée")
        
        if evaluation.statut != StatutEvaluation.VALIDEE:
            raise ValueError("L'évaluation doit être validée pour générer un certificat")
        
        # 🔧 Vérifier qu'il n'y a pas déjà de certificat pour cette évaluation
        certificat_existant = db.query(Certificat).filter(
            Certificat.evaluation_id == evaluation_id
        ).first()
        if certificat_existant:
            return {
                "success": True,
                "message": "Un certificat existe déjà pour cette évaluation",
                "certificat": certificat_existant,
                "code_unique": certificat_existant.code_unique,
                "deja_genere": True
            }
        
        # 🔧 Vérifier s'il y a déjà un certificat pour cette candidature
        stage = evaluation.stage
        if stage.candidature_id:
            certificat_candidature = db.query(Certificat).filter(
                Certificat.candidature_id == stage.candidature_id
            ).first()
            if certificat_candidature:
                return {
                    "success": True,
                    "message": f"Un certificat existe déjà pour la candidature de {stage.stagiaire.prenom} {stage.stagiaire.nom}",
                    "certificat": certificat_candidature,
                    "code_unique": certificat_candidature.code_unique,
                    "deja_genere": True
                }
        
        # 🔧 Récupérer les données nécessaires avec vérifications
        if not stage:
            raise ValueError("Stage non trouvé pour cette évaluation")
        
        stagiaire = stage.stagiaire
        if not stagiaire:
            raise ValueError("Stagiaire non trouvé pour ce stage")
        
        entreprise = stage.entreprise
        if not entreprise:
            raise ValueError("Entreprise non trouvée pour ce stage")
        
        evaluateur = evaluation.evaluateur
        if not evaluateur:
            raise ValueError("Évaluateur non trouvé pour cette évaluation")
        
        # Récupérer le titre du stage
        titre_stage = "Stage"
        if stage.candidature and stage.candidature.offre:
            titre_stage = stage.candidature.offre.titre
        elif stage.description:
            titre_stage = stage.description
        
        # Calculer la durée du stage
        duree_jours = (stage.date_fin - stage.date_debut).days
        if duree_jours <= 0:
            duree_jours = 1  # Minimum 1 jour
        
        try:
            # Générer le code unique et QR code
            code_unique = CodeUniqueService.generer_code_certificat(db)
            qr_code_data = QRCodeService.generer_qr_code(code_unique, base_url)
            
            # 🔧 Créer le certificat avec les vraies données
            certificat = Certificat(
                code_unique=code_unique,
                titre_stage=titre_stage,
                date_debut_stage=stage.date_debut,
                date_fin_stage=stage.date_fin,
                duree_stage_jours=duree_jours,
                note_finale=evaluation.note_globale,
                mention=CertificatService.calculer_mention(evaluation.note_globale),
                nom_stagiaire=stagiaire.nom,
                prenom_stagiaire=stagiaire.prenom,
                nom_entreprise=entreprise.raison_social,
                secteur_entreprise=entreprise.secteur_activite or "Non spécifié",
                nom_evaluateur=evaluateur.nom,
                prenom_evaluateur=evaluateur.prenom,
                poste_evaluateur=evaluateur.poste or "Évaluateur",
                qr_code_data=qr_code_data,
                evaluation_id=evaluation_id,
                candidature_id=stage.candidature_id,  # 🔧 VRAIE candidature_id
                stage_id=stage.id,
                entreprise_id=entreprise.id,  # 🔧 VRAIE entreprise_id
                generateur_id=generateur_id,
                statut=StatutCertificat.GENERE
            )
            
            db.add(certificat)
            db.commit()
            db.refresh(certificat)
            
            return {
                "success": True,
                "message": "Certificat généré avec succès",
                "certificat": certificat,
                "code_unique": certificat.code_unique,
                "deja_genere": False
            }
            
        except IntegrityError as e:
            # 🔧 Gestion des erreurs de contrainte unique
            db.rollback()
            
            error_msg = str(e)
            print(f"🔧 Erreur IntegrityError: {error_msg}")
            
            if "certificat_candidature_id_key" in error_msg:
                # Récupérer le certificat existant
                certificat_existant = db.query(Certificat).filter(
                    Certificat.candidature_id == stage.candidature_id
                ).first()
                
                return {
                    "success": True,
                    "message": f"Un certificat existe déjà pour la candidature de {stagiaire.prenom} {stagiaire.nom}",
                    "certificat": certificat_existant,
                    "code_unique": certificat_existant.code_unique if certificat_existant else None,
                    "deja_genere": True
                }
            elif "certificat_evaluation_id_key" in error_msg:
                certificat_existant = db.query(Certificat).filter(
                    Certificat.evaluation_id == evaluation_id
                ).first()
                
                return {
                    "success": True,
                    "message": "Un certificat existe déjà pour cette évaluation",
                    "certificat": certificat_existant,
                    "code_unique": certificat_existant.code_unique if certificat_existant else None,
                    "deja_genere": True
                }
            else:
                raise ValueError(f"Erreur lors de la création du certificat: {str(e)}")
                
        except Exception as e:
            db.rollback()
            print(f"🔧 Erreur générale: {str(e)}")
            raise ValueError(f"Erreur lors de la génération du certificat: {str(e)}")
    
    @staticmethod
    def calculer_mention(note: float) -> str:
        """Calcule la mention basée sur la note."""
        if note >= 9:
            return "Excellent"
        elif note >= 8:
            return "Très Bien"
        elif note >= 7:
            return "Bien"
        elif note >= 6:
            return "Assez Bien"
        elif note >= 5:
            return "Passable"
        else:
            return "Insuffisant"
    
    @staticmethod
    def verifier_certificat(db: Session, code_unique: str) -> Optional[Certificat]:
        """Vérifie l'authenticité d'un certificat."""
        certificat = db.query(Certificat).filter(
            Certificat.code_unique == code_unique
        ).first()
        
        if certificat:
            certificat.incrementer_verifications()
            db.commit()
        
        return certificat
    
    @staticmethod
    def marquer_comme_telecharge(db: Session, certificat_id: int):
        """Marque un certificat comme téléchargé."""
        certificat = db.query(Certificat).filter(Certificat.id == certificat_id).first()
        if certificat:
            certificat.statut = StatutCertificat.TELECHARGE
            certificat.date_dernier_telechargement = func.now()
            db.commit()

class VerificationService:
    """Service pour la vérification des certificats."""
    
    @staticmethod
    def verifier_par_qr_code(db: Session, code_unique: str) -> Dict[str, Any]:
        """Vérifie un certificat via son code QR."""
        certificat = CertificatService.verifier_certificat(db, code_unique)
        
        if not certificat:
            return {
                "valide": False,
                "message": "Certificat non trouvé ou invalide",
                "certificat": None
            }
        
        return {
            "valide": True,
            "message": "Certificat valide",
            "certificat": certificat,
            "verification_numero": certificat.nombre_verifications
        }
    
    
    # class CertificatService:
#     """Service pour gérer les certificats."""
    
#     @staticmethod
#     def generer_certificat(
#         db: Session, 
#         evaluation_id: int, 
#         generateur_id: int,
#         base_url: str = "http://localhost:8000"
#     ) -> Certificat:
#         """Génère un certificat à partir d'une évaluation validée."""
        
#         evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
#         if not evaluation:
#             raise ValueError("Évaluation non trouvée")
        
#         if evaluation.statut != StatutEvaluation.VALIDEE:
#             raise ValueError("L'évaluation doit être validée pour générer un certificat")
        
#         # Vérifier qu'il n'y a pas déjà de certificat
#         certificat_existant = db.query(Certificat).filter(
#             Certificat.evaluation_id == evaluation_id
#         ).first()
#         if certificat_existant:
#             raise ValueError("Un certificat a déjà été généré pour cette évaluation")
        
#         # Récupérer les données nécessaires
#         stage = evaluation.stage
#         generateur = db.query(Utilisateur).filter(Utilisateur.id == generateur_id).first()
        
#         # Calculer la durée du stage
#         duree_jours = (stage.date_fin - stage.date_debut).days
        
#         # Générer le code unique et QR code
#         code_unique = CodeUniqueService.generer_code_certificat(db)
#         qr_code_data = QRCodeService.generer_qr_code(code_unique, base_url)
        
#         # Créer le certificat
#         certificat = Certificat(
#             code_unique=code_unique,
#             titre_stage=f"Stage {stage.description}",
#             date_debut_stage=stage.date_debut,
#             date_fin_stage=stage.date_fin,
#             duree_stage_jours=duree_jours,
#             note_finale=evaluation.note_globale,
#             mention=CertificatService.calculer_mention(evaluation.note_globale),
#             nom_stagiaire="Stagiaire",  # À adapter selon tes relations
#             prenom_stagiaire="Test",
#             nom_entreprise="Entreprise Test",
#             secteur_entreprise="Informatique",
#             nom_evaluateur=generateur.nom if generateur else "Évaluateur",
#             prenom_evaluateur=generateur.prenom if generateur else "Test",
#             poste_evaluateur="Responsable RH",
#             qr_code_data=qr_code_data,
#             evaluation_id=evaluation_id,
#             candidature_id=1,  # À adapter
#             stage_id=stage.id,
#             entreprise_id=1,  # À adapter
#             generateur_id=generateur_id,
#             statut=StatutCertificat.GENERE
#         )
        
#         db.add(certificat)
#         db.commit()
#         db.refresh(certificat)
#         return certificat
    
#     @staticmethod
#     def calculer_mention(note: float) -> str:
#         """Calcule la mention basée sur la note."""
#         if note >= 9:
#             return "Excellent"
#         elif note >= 8:
#             return "Très Bien"
#         elif note >= 7:
#             return "Bien"
#         elif note >= 6:
#             return "Assez Bien"
#         elif note >= 5:
#             return "Passable"
#         else:
#             return "Insuffisant"
    
#     @staticmethod
#     def verifier_certificat(db: Session, code_unique: str) -> Optional[Certificat]:
#         """Vérifie l'authenticité d'un certificat."""
#         certificat = db.query(Certificat).filter(
#             Certificat.code_unique == code_unique
#         ).first()
        
#         if certificat:
#             certificat.incrementer_verifications()
#             db.commit()
        
#         return certificat
    
#     @staticmethod
#     def marquer_comme_telecharge(db: Session, certificat_id: int):
#         """Marque un certificat comme téléchargé."""
#         certificat = db.query(Certificat).filter(Certificat.id == certificat_id).first()
#         if certificat:
#             certificat.statut = StatutCertificat.TELECHARGE
#             certificat.date_dernier_telechargement = func.now()
#             db.commit()

# class VerificationService:
#     """Service pour la vérification des certificats."""
    
#     @staticmethod
#     def verifier_par_qr_code(db: Session, code_unique: str) -> Dict[str, Any]:
#         """Vérifie un certificat via son code QR."""
#         certificat = CertificatService.verifier_certificat(db, code_unique)
        
#         if not certificat:
#             return {
#                 "valide": False,
#                 "message": "Certificat non trouvé ou invalide",
#                 "certificat": None
#             }
        
#         return {
#             "valide": True,
#             "message": "Certificat valide",
#             "certificat": certificat,
#             "verification_numero": certificat.nombre_verifications
#         }
