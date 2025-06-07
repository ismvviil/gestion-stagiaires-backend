from sqlalchemy import Column, Integer, ForeignKey, String, Date, Text
from sqlalchemy.orm import relationship
from app.models.utilisateur import Utilisateur

class Stagiaire(Utilisateur):
    __tablename__ = 'stagiaire'
    
    id = Column(Integer, ForeignKey('utilisateur.id'), primary_key=True)
    photo = Column(String, nullable=True)  # Chemin vers la photo ou URL
    

    # 🆕 NOUVEAUX CHAMPS pour le profil complet
    telephone = Column(String(20), nullable=True)
    date_naissance = Column(Date, nullable=True)

    # Adresse
    adresse = Column(String(255), nullable=True)
    ville = Column(String(100), nullable=True)
    code_postal = Column(String(10), nullable=True)

    # Formation et compétences
    niveau_etudes = Column(String(100), nullable=True)  # "Bac+3", "Master", etc.
    specialite = Column(String(150), nullable=True)     # "Informatique", "Marketing", etc.

    # CV et compétences
    cv_filename = Column(String(255), nullable=True)    # Nom du fichier CV uploadé
    competences_manuelles = Column(Text, nullable=True) # Compétences saisies par l'utilisateur
    competences_extraites = Column(Text, nullable=True) # Compétences extraites automatiquement du CV

    # Candidatures soumises
    candidatures = relationship("Candidature", back_populates="stagiaire")
    stages = relationship("Stage", back_populates="stagiaire")

    
    # Missions suivies
    # missions = relationship("Mission", back_populates="stagiaire")
    
    # Feedback reçus
    # feedbacks = relationship("Evaluation", back_populates="stagiaire")
    
    # Historique des stages
    # historiques = relationship("HistoriqueStage", back_populates="stagiaire")
    
    # Remplacer la ligne commentée par :
    
    __mapper_args__ = {
        'polymorphic_identity': 'stagiaire',
    }

    def get_all_competences(self):
        """Récupère toutes les compétences (manuelles + extraites)."""
        competences = []
        
        if self.competences_manuelles:
            competences.extend([c.strip() for c in self.competences_manuelles.split(',')])
        
        if self.competences_extraites:
            competences.extend([c.strip() for c in self.competences_extraites.split(',')])
        
        # Supprimer les doublons et retourner
        return list(set(filter(None, competences)))
    
    def add_competence_extraite(self, competence):
        """Ajouter une compétence extraite du CV."""
        if self.competences_extraites:
            competences = [c.strip() for c in self.competences_extraites.split(',')]
            if competence not in competences:
                competences.append(competence)
                self.competences_extraites = ', '.join(competences)
        else:
            self.competences_extraites = competence