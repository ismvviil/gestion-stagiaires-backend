from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Enum, Boolean ,  Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel

class StatusStage(enum.Enum):
    """Énumération des statuts possibles pour un stage."""
    EN_ATTENTE = "en_attente"  # Stage créé mais pas encore commencé
    EN_COURS = "en_cours"      # Stage en cours
    TERMINE = "termine"        # Stage terminé avec succès
    INTERROMPU = "interrompu"  # Stage interrompu avant la fin
    SUSPENDU = "suspendu"      # Stage temporairement suspendu

class Stage(BaseModel):
    """Modèle pour les stages effectifs."""

    # Informations du stage
    date_debut = Column(DateTime(timezone=True), nullable=False)
    date_fin = Column(DateTime(timezone=True), nullable=False)
    # status = Column(Enum(StatusStage), default=StatusStage.EN_ATTENTE)
    status = Column(String(20), default=StatusStage.EN_ATTENTE.value)

    # statut = Column(
    #     SQLEnum(
    #         StatutEvaluation,
    #         name='statutevaluation',
    #         create_constraint=True,
    #         validate_strings=True
    #     ),
    #     default=StatutEvaluation.BROUILLON
    # )
    # Objectifs et description
    objectifs = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Suivi
    date_debut_reel = Column(DateTime(timezone=True), nullable=True)
    date_fin_reel = Column(DateTime(timezone=True), nullable=True)

    # Commentaires
    commentaires_entreprise = Column(Text, nullable=True)
    commentaires_stagiaire = Column(Text, nullable=True)

    # Évaluation finale
    note_finale = Column(Integer, nullable=True)  # Note sur 20
    certificat_genere = Column(Boolean, default=False)

    # Clés étrangères
    candidature_id = Column(Integer, ForeignKey("candidature.id"), nullable=False, unique=True)
    stagiaire_id = Column(Integer, ForeignKey("stagiaire.id"), nullable=False)
    entreprise_id = Column(Integer, ForeignKey("entreprise.id"), nullable=False)
    recruteur_id = Column(Integer, ForeignKey("recruteur.id"), nullable=False)  # Encadrant principal

    # Relations
    candidature = relationship("Candidature", back_populates="stage")
    stagiaire = relationship("Stagiaire", back_populates="stages")
    entreprise = relationship("Entreprise", back_populates="stages")
    recruteur = relationship("Recruteur", back_populates="stages_encadres")

    # Missions du stage
    missions = relationship("Mission", back_populates="stage", cascade="all, delete-orphan")

    # Dans Stage (app/models/stage.py) - ajouter cette relation :
    evaluation = relationship("Evaluation", back_populates="stage", uselist=False)
    
    def commencer_stage(self):
        """Commencer le stage."""
        self.status = StatusStage.EN_COURS
        self.date_debut_reel = func.now()

    def terminer_stage(self, note_finale=None, commentaires=None):
        """Terminer le stage."""
        self.status = StatusStage.TERMINE
        self.date_fin_reel = func.now()
        if note_finale:
            self.note_finale = note_finale
        if commentaires:
            self.commentaires_entreprise = commentaires

    def interrompre_stage(self, commentaires=None):
        """Interrompre le stage."""
        self.status = StatusStage.INTERROMPU
        self.date_fin_reel = func.now()
        if commentaires:
            self.commentaires_entreprise = commentaires

    def suspendre_stage(self, commentaires=None):
        """Suspendre temporairement le stage."""
        self.status = StatusStage.SUSPENDU
        if commentaires:
            self.commentaires_entreprise = commentaires