from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel
from app.schemas.mission import StatusMissionEnum , PrioriteMissionEnum
# class StatusMission(enum.Enum):
#     """Énumération des statuts possibles pour une mission."""
#     A_FAIRE = "a_faire"        # Mission assignée mais pas commencée
#     EN_COURS = "en_cours"      # Mission en cours de réalisation
#     EN_REVISION = "en_revision" # Mission soumise, en attente de validation
#     TERMINEE = "terminee"      # Mission terminée et validée
#     ANNULEE = "annulee"        # Mission annulée

# class PrioriteMission(enum.Enum):
#     """Énumération des priorités pour une mission."""
#     BASSE = "basse"
#     NORMALE = "normale"
#     HAUTE = "haute"
#     URGENTE = "urgente"

class Mission(BaseModel):
    """Modèle pour les missions assignées aux stagiaires."""
    
    # Informations de base
    titre = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    objectifs = Column(Text, nullable=True)

    # Dates et délais
    date_assignation = Column(DateTime(timezone=True), server_default=func.now())
    date_debut_prevue = Column(DateTime(timezone=True), nullable=True)
    date_fin_prevue = Column(DateTime(timezone=True), nullable=True)
    date_debut_reel = Column(DateTime(timezone=True), nullable=True)
    date_fin_reel = Column(DateTime(timezone=True), nullable=True)

    # Statut et priorité
    status = Column(String, default='a_faire')
    priorite = Column(String, default='normale')

    # Progression
    pourcentage_completion = Column(Integer, default=0)  # 0 à 100

    # Ressources et outils
    ressources_necessaires = Column(Text, nullable=True)
    outils_utilises = Column(Text, nullable=True)

    # Évaluation
    note_mission = Column(Integer, nullable=True)  # Note sur 20
    feedback_recruteur = Column(Text, nullable=True)
    feedback_stagiaire = Column(Text, nullable=True)

    # Livrables
    livrables_attendus = Column(Text, nullable=True)
    livrables_fournis = Column(Text, nullable=True)

    # Clés étrangères
    stage_id = Column(Integer, ForeignKey("stage.id"), nullable=False)
    assigne_par_id = Column(Integer, ForeignKey("recruteur.id"), nullable=False)

    # Relations
    stage = relationship("Stage", back_populates="missions")
    assigne_par = relationship("Recruteur", back_populates="missions_assignees")

    def commencer_mission(self):
        """Commencer la mission."""
        self.status = StatusMissionEnum.EN_COURS
        self.date_debut_reel = func.now()
    
    def soumettre_mission(self, livrables=None, feedback_stagiaire=None):
        """Soumettre la mission pour révision."""
        self.status = StatusMissionEnum.EN_REVISION
        self.pourcentage_completion = 100
        if livrables:
            self.livrables_fournis = livrables
        if feedback_stagiaire:
            self.feedback_stagiaire = feedback_stagiaire


    def valider_mission(self, note=None, feedback=None):
        """Valider la mission (par le recruteur)."""
        self.status = StatusMissionEnum.TERMINEE
        self.date_fin_reel = func.now()
        if note:
            self.note_mission = note
        if feedback:
            self.feedback_recruteur = feedback
    
    def rejeter_mission(self, feedback):
        """Rejeter la mission et la remettre en cours."""
        self.status = StatusMissionEnum.EN_COURS
        self.pourcentage_completion = max(0, self.pourcentage_completion - 20)
        self.feedback_recruteur = feedback

    def annuler_mission(self, raison):
        """Annuler la mission."""
        self.status = StatusMissionEnum.ANNULEE
        self.feedback_recruteur = raison
    
    def mettre_a_jour_progression(self, pourcentage):
        """Mettre à jour le pourcentage de completion."""
        if 0 <= pourcentage <= 100:
            self.pourcentage_completion = pourcentage
            if pourcentage == 100 and self.status == StatusMissionEnum.EN_COURS:
                self.status = StatusMissionEnum.EN_REVISION