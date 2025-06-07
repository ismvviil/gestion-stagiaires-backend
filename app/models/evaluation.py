from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel
import enum
import uuid
from datetime import datetime

class TypeCritere(enum.Enum):
    """Types de critères d'évaluation."""
    COMPETENCE_TECHNIQUE = "competence_technique"
    COMPORTEMENT = "comportement"
    COMMUNICATION = "communication"
    INITIATIVE = "initiative"
    PONCTUALITE = "ponctualite"
    TRAVAIL_EQUIPE = "travail_equipe"
    ADAPTATION = "adaptation"
    AUTRE = "autre"

class CritereEvaluation(BaseModel):
    """Modèle pour les critères d'évaluation."""
    
    nom = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    # type_critere = Column(String, nullable=False)
    type_critere = Column(
        SQLEnum(
            TypeCritere,
            name='typecritere',           # Nom exact en PostgreSQL
            create_constraint=False,      # Ne pas créer, utiliser l'existant
            validate_strings=True,       # Valider les chaînes
            values_callable=lambda x: [e.value for e in x]  # Utiliser les valeurs enum
        ),
        nullable=False
    )
    poids = Column(Float, default=1.0)  # Coefficient pour la note finale
    actif = Column(Boolean, default=True)
    
    # Qui a créé ce critère (entreprise spécifique ou système)
    entreprise_id = Column(Integer, ForeignKey("entreprise.id"), nullable=True)
    est_global = Column(Boolean, default=False)  # True = critère système, False = critère entreprise
    
    # Relations
    entreprise = relationship("Entreprise", back_populates="criteres_evaluation")
    details_evaluations = relationship("DetailEvaluation", back_populates="critere")

class StatutEvaluation(enum.Enum):
    """Statuts d'une évaluation."""
    BROUILLON = "brouillon"
    TERMINEE = "terminee"
    VALIDEE = "validee"

class Evaluation(BaseModel):
    """Modèle pour les évaluations de stage."""
    # Informations générales
    # statut = Column(SQLEnum(StatutEvaluation), default=StatutEvaluation.BROUILLON)
    statut = Column(
        SQLEnum(
            StatutEvaluation,
            name='statutevaluation',
            create_constraint=True,
            validate_strings=True
        ),
        default=StatutEvaluation.BROUILLON
    )
    note_globale = Column(Float, nullable=True)  # Note calculée automatiquement
    commentaire_general = Column(Text, nullable=True)

    # Recommandations
    points_forts = Column(Text, nullable=True)
    points_amelioration = Column(Text, nullable=True)
    recommandations = Column(Text, nullable=True)

    # Embauche potentielle
    recommande_embauche = Column(Boolean, nullable=True)

    # Dates
    date_evaluation = Column(DateTime(timezone=True), server_default=func.now())
    date_validation = Column(DateTime(timezone=True), nullable=True)
    
    # Clés étrangères
    stage_id = Column(Integer, ForeignKey("stage.id"), nullable=False, unique=True)
    evaluateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)

    # Relations
    stage = relationship("Stage", back_populates="evaluation")
    evaluateur = relationship("Utilisateur")  # RH ou Recruteur
    details = relationship("DetailEvaluation", back_populates="evaluation", cascade="all, delete-orphan")
    certificat = relationship("Certificat", back_populates="evaluation", uselist=False)

    # def calculer_note_globale(self):
    #     """Calcule la note globale basée sur les détails d'évaluation."""
    #     if not self.details:
    #         return None
        
    #     total_poids = sum(detail.critere.poids for detail in self.details)
    #     if total_poids == 0:
    #         return None
        
    #     note_ponderee = sum(detail.note * detail.critere.poids for detail in self.details)
    #     self.note_globale = round(note_ponderee / total_poids, 2)
    #     return self.note_globale

    def calculer_note_globale(self):
        """Calcule la note globale basée sur les détails d'évaluation."""
        if not self.details:
            return None
    
        # 🔧 FIX : Filtrer les critères actifs
        details_actifs = [d for d in self.details if d.critere and d.critere.actif]
        if not details_actifs:
            return None
    
        total_poids = sum(detail.critere.poids for detail in details_actifs)
        if total_poids == 0:
            return None
    
        note_ponderee = sum(detail.note * detail.critere.poids for detail in details_actifs)
        self.note_globale = round(note_ponderee / total_poids, 2)
        return self.note_globale
    
    def valider_evaluation(self):
        """Valider l'évaluation."""
        self.statut = StatutEvaluation.VALIDEE
        self.date_validation = func.now()

class DetailEvaluation(BaseModel):
    """Modèle pour le détail d'une évaluation par critère."""
    
    note = Column(Integer, nullable=False)  # Note de 1 à 10
    commentaire = Column(Text, nullable=True)

     # Clés étrangères
    evaluation_id = Column(Integer, ForeignKey("evaluation.id"), nullable=False)
    critere_id = Column(Integer, ForeignKey("critereevaluation.id"), nullable=False)

    # Relations
    evaluation = relationship("Evaluation", back_populates="details")
    critere = relationship("CritereEvaluation", back_populates="details_evaluations")

    # Contrainte unique
    __table_args__ = (
        {'schema': None},  # Peut être ajusté selon votre configuration
    )

class StatutCertificat(enum.Enum):
    """Statuts d'un certificat."""
    GENERE = "genere"
    TELECHARGE = "telecharge"
    VERIFIE = "verifie"

class Certificat(BaseModel):
    """Modèle pour les certificats de stage."""
    
    # Code unique pour vérification
    code_unique = Column(String, unique=True, nullable=False, index=True)

    # Informations du certificat
    titre_stage = Column(String, nullable=False)
    date_debut_stage = Column(DateTime(timezone=True), nullable=False)
    date_fin_stage = Column(DateTime(timezone=True), nullable=False)
    duree_stage_jours = Column(Integer, nullable=False)

    # Résultats
    note_finale = Column(Float, nullable=False)
    mention = Column(String, nullable=True)  # Excellent, Très bien, Bien, etc.
    
    # Informations stagiaire (dénormalisées pour historique)
    nom_stagiaire = Column(String, nullable=False)
    prenom_stagiaire = Column(String, nullable=False)

    # Informations entreprise (dénormalisées pour historique)
    nom_entreprise = Column(String, nullable=False)
    secteur_entreprise = Column(String, nullable=False)

    # Informations évaluateur (dénormalisées pour historique)
    nom_evaluateur = Column(String, nullable=False)
    prenom_evaluateur = Column(String, nullable=False)
    poste_evaluateur = Column(String, nullable=False)

    # Métadonnées
    # statut = Column(SQLEnum(StatutCertificat), default=StatutCertificat.GENERE)
    statut = Column(
        SQLEnum(
            StatutCertificat,
            name='statutcertificat',
            create_constraint=True,
            validate_strings=True
        ),
        default=StatutCertificat.GENERE
    )
    date_generation = Column(DateTime(timezone=True), server_default=func.now())
    date_dernier_telechargement = Column(DateTime(timezone=True), nullable=True)
    nombre_verifications = Column(Integer, default=0)

    # QR Code et PDF
    qr_code_data = Column(Text, nullable=True)  # Data du QR code
    chemin_pdf = Column(String, nullable=True)  # Chemin vers le PDF si stocké

    # Clés étrangères
    evaluation_id = Column(Integer, ForeignKey("evaluation.id"), nullable=False, unique=True)
    candidature_id = Column(Integer, ForeignKey("candidature.id"), nullable=False, unique=True)
    stage_id = Column(Integer, ForeignKey("stage.id"), nullable=False)
    entreprise_id = Column(Integer, ForeignKey("entreprise.id"), nullable=False)
    generateur_id = Column(Integer, ForeignKey("utilisateur.id"), nullable=False)  # RH qui a généré

    # Relations
    evaluation = relationship("Evaluation", back_populates="certificat")
    candidature = relationship("Candidature", back_populates="certificat")
    stage = relationship("Stage")
    entreprise = relationship("Entreprise")
    generateur = relationship("Utilisateur")  # RH ou Recruteur qui a généré le certificat

    @classmethod
    def generer_code_unique(cls, annee: int = None) -> str:
        """Génère un code unique pour le certificat."""
        if annee is None:
            annee = datetime.now().year
        
        # Format: CERT-YYYY-XXXXXXXX (8 caractères aléatoires)
        code_aleatoire = str(uuid.uuid4()).replace('-', '').upper()[:8]
        return f"CERT-{annee}-{code_aleatoire}"
    
    def calculer_mention(self) -> str:
        """Calcule la mention basée sur la note finale."""
        if self.note_finale >= 9:
            return "Excellent"
        elif self.note_finale >= 8:
            return "Très Bien"
        elif self.note_finale >= 7:
            return "Bien"
        elif self.note_finale >= 6:
            return "Assez Bien"
        elif self.note_finale >= 5:
            return "Passable"
        else:
            return "Insuffisant"
        
    def incrementer_verifications(self):
        """Incrémente le compteur de vérifications."""
        self.nombre_verifications += 1