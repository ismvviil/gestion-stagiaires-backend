from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel
from app.models.stage import Stage

class StatusCandidature(enum.Enum):
    """Énumération des statuts possibles pour une candidature."""
    EN_ATTENTE = "en_attente"
    EN_COURS = "en_cours"
    ACCEPTEE = "acceptee"
    REFUSEE = "refusee"
    RETIREE = "retiree"

class Candidature(BaseModel):
    """Modèle pour les candidatures aux offres de stage."""

     # Informations de la candidature
    cv = Column(String, nullable=True)  # Chemin vers le fichier CV
    lettre_motivation = Column(Text, nullable=True)
    competences = Column(Text, nullable=True)  # Compétences du candidat
    niveau_etudes = Column(String, nullable=True)
    status = Column(Enum(StatusCandidature), default=StatusCandidature.EN_ATTENTE)
    date_debut = Column(DateTime(timezone=True), server_default=func.now())
    date_fin = Column(DateTime(timezone=True), nullable=True)

     # Commentaires et notes
    commentaires_candidat = Column(Text, nullable=True)  # Message du candidat
    commentaires_recruteur = Column(Text, nullable=True)  # Notes du recruteur
    note_recruteur = Column(Integer, nullable=True)  # Note sur 5 ou 10

    # Clés étrangères
    stagiaire_id = Column(Integer, ForeignKey("stagiaire.id"), nullable=False)
    offre_id = Column(Integer, ForeignKey("offre.id"), nullable=False)
    recruteur_id = Column(Integer, ForeignKey("recruteur.id"), nullable=True)

    # Relations
    stagiaire = relationship("Stagiaire", back_populates="candidatures")
    offre = relationship("Offre", back_populates="candidatures")
    recruteur = relationship("Recruteur", back_populates="candidatures")

    # Ajouter cette ligne dans la classe Candidature
    stage = relationship("Stage", back_populates="candidature", uselist=False)

    certificat = relationship("Certificat", back_populates="candidature", uselist=False)


    def accepter(self, recruteur_id, commentaires=None):
        """Accepter la candidature et créer automatiquement un stage."""
        from app.models.stage import Stage, StatusStage

        self.status = StatusCandidature.ACCEPTEE
        self.recruteur_id = recruteur_id
        self.date_fin = func.now()
        if commentaires:
            self.commentaires_recruteur = commentaires

        # Créer automatiquement le stage
        stage = Stage(
            candidature_id=self.id,
            stagiaire_id=self.stagiaire_id,
            entreprise_id=self.offre.entreprise_id,
            recruteur_id=recruteur_id,
            date_debut=self.offre.date_debut,  # Utilise les dates de l'offre
            date_fin=self.offre.date_fin,
            status=StatusStage.EN_ATTENTE,
            description=f"Stage pour l'offre: {self.offre.titre}",
            objectifs=self.offre.description  # Utilise la description de l'offre comme objectifs initiaux
        )

        return stage  # Retourne le stage créé pour que l'API puisse le sauvegarder


    def refuser(self, recruteur_id, commentaires=None):
        """Refuser la candidature."""
        self.status = StatusCandidature.REFUSEE
        self.recruteur_id = recruteur_id
        self.date_fin = func.now()
        if commentaires:
            self.commentaires_recruteur = commentaires

    def mettre_en_cours(self, recruteur_id, commentaires=None):
        """Mettre la candidature en cours de traitement."""
        self.status = StatusCandidature.EN_COURS
        self.recruteur_id = recruteur_id
        # ⚠️ AJOUTEZ CETTE LIGNE QUI MANQUAIT :
        if commentaires:
            self.commentaires_recruteur = commentaires


    def retirer(self):
        """Permettre au stagiaire de retirer sa candidature."""
        self.status = StatusCandidature.RETIREE
        self.date_fin = func.now()