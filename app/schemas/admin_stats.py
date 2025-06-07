from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class StatistiquesGlobales(BaseModel):
    """Statistiques globales de la plateforme."""
    
    # Utilisateurs
    nombre_total_utilisateurs: int
    nombre_stagiaires: int
    nombre_recruteurs: int
    nombre_rh: int
    nombre_admins: int

    # Entreprises
    nombre_entreprises: int
    entreprises_actives: int

    # Offres et candidatures
    nombre_offres_total: int
    nombre_offres_actives: int
    nombre_candidatures_total: int
    nombre_candidatures_acceptees: int
    
    # Stages et évaluations
    nombre_stages_total: int
    nombre_stages_termines: int
    nombre_evaluations_total: int
    nombre_certificats_generes: int

    # Taux de conversion
    taux_acceptation_candidatures: Optional[float] = None
    taux_completion_stages: Optional[float] = None
    note_moyenne_globale: Optional[float] = None


class StatistiquesTemporelles(BaseModel):
    """Évolution temporelle des métriques."""
    
    mois: str  # Format: "2024-01", "2024-02", etc.
    nouvelles_inscriptions: int
    nouvelles_offres: int
    nouvelles_candidatures: int
    stages_commences: int
    stages_termines: int

class StatistiquesEntreprises(BaseModel):
    """Statistiques par entreprise."""
    
    entreprise_id: int
    nom_entreprise: str
    secteur: str
    nombre_recruteurs: int
    nombre_offres: int
    nombre_candidatures_recues: int
    nombre_stages_encadres: int
    note_moyenne_evaluations: Optional[float] = None

class StatistiquesSecteurs(BaseModel):
    """Répartition par secteur d'activité."""
    
    secteur: str
    nombre_entreprises: int
    nombre_offres: int
    nombre_stages: int
    note_moyenne: Optional[float] = None

class UtilisateurDetaille(BaseModel):
    """Informations détaillées d'un utilisateur pour l'admin."""
    
    id: int
    email: str
    nom: str
    prenom: str
    type: str
    actif: bool
    created_at: datetime
    
    # Informations spécifiques selon le type
    entreprise_nom: Optional[str] = None
    nombre_candidatures: Optional[int] = None  # Pour stagiaires
    nombre_offres: Optional[int] = None        # Pour recruteurs
    derniere_connexion: Optional[datetime] = None