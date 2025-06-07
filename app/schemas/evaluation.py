# app/schemas/evaluation.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

from app.schemas.base import BaseSchema

# Enums
class TypeCritereEnum(str, Enum):
    COMPETENCE_TECHNIQUE = "competence_technique"
    COMPORTEMENT = "comportement"
    COMMUNICATION = "communication"
    INITIATIVE = "initiative"
    PONCTUALITE = "ponctualite"
    TRAVAIL_EQUIPE = "travail_equipe"
    ADAPTATION = "adaptation"
    AUTRE = "autre"

class StatutEvaluationEnum(str, Enum):
    BROUILLON = "brouillon"
    TERMINEE = "terminee"
    VALIDEE = "validee"

class StatutCertificatEnum(str, Enum):
    GENERE = "genere"
    TELECHARGE = "telecharge"
    VERIFIE = "verifie"

# ============================================================================
# CRITÈRES D'ÉVALUATION
# ============================================================================

class CritereEvaluationBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    type_critere: TypeCritereEnum
    poids: float = Field(default=1.0, ge=0.1, le=5.0)
    actif: bool = True
    est_global: bool = False

class CritereEvaluationCreate(CritereEvaluationBase):
    entreprise_id: Optional[int] = None

class CritereEvaluationUpdate(BaseModel):
    nom: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    type_critere: Optional[TypeCritereEnum] = None
    poids: Optional[float] = Field(None, ge=0.1, le=5.0)
    actif: Optional[bool] = None

class CritereEvaluation(BaseSchema, CritereEvaluationBase):
    entreprise_id: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================================================
# DÉTAILS D'ÉVALUATION
# ============================================================================

class DetailEvaluationBase(BaseModel):
    note: int = Field(..., ge=1, le=10)
    commentaire: Optional[str] = None

class DetailEvaluationCreate(DetailEvaluationBase):
    critere_id: int

class DetailEvaluationUpdate(BaseModel):
    note: Optional[int] = Field(None, ge=1, le=10)
    commentaire: Optional[str] = None

class DetailEvaluation(BaseSchema, DetailEvaluationBase):
    evaluation_id: int
    critere_id: int
    critere: CritereEvaluation

    class Config:
        from_attributes = True

# ============================================================================
# ÉVALUATIONS
# ============================================================================

class EvaluationBase(BaseModel):
    commentaire_general: Optional[str] = None
    points_forts: Optional[str] = None
    points_amelioration: Optional[str] = None
    recommandations: Optional[str] = None
    recommande_embauche: Optional[bool] = None

class EvaluationCreate(EvaluationBase):
    stage_id: int
    details: List[DetailEvaluationCreate] = []

    @validator('details')
    def valider_details(cls, v):
        if len(v) == 0:
            raise ValueError('Au moins un critère doit être évalué')
        
        # Vérifier l'unicité des critères
        criteres_ids = [detail.critere_id for detail in v]
        if len(criteres_ids) != len(set(criteres_ids)):
            raise ValueError('Chaque critère ne peut être évalué qu\'une seule fois')
        
        return v
    
class EvaluationUpdate(EvaluationBase):
    details: Optional[List[DetailEvaluationCreate]] = None

class EvaluationValidation(BaseModel):
    """Schéma pour valider une évaluation."""
    valider: bool = True

class Evaluation(BaseSchema, EvaluationBase):
    statut: StatutEvaluationEnum
    note_globale: Optional[float] = None
    date_evaluation: datetime
    date_validation: Optional[datetime] = None
    stage_id: int
    evaluateur_id: int
    details: List[DetailEvaluation] = []

    class Config:
        from_attributes = True

# ============================================================================
# CERTIFICATS
# ============================================================================

class CertificatBase(BaseModel):
    titre_stage: str
    date_debut_stage: datetime
    date_fin_stage: datetime
    duree_stage_jours: int
    note_finale: float = Field(..., ge=0, le=10)
    mention: Optional[str] = None
    nom_stagiaire: str
    prenom_stagiaire: str
    nom_entreprise: str
    secteur_entreprise: str
    nom_evaluateur: str
    prenom_evaluateur: str
    poste_evaluateur: str

class CertificatGeneration(BaseModel):
    """Schéma pour générer un certificat."""
    evaluation_id: int


class Certificat(BaseSchema, CertificatBase):
    code_unique: str
    statut: StatutCertificatEnum
    date_generation: datetime
    date_dernier_telechargement: Optional[datetime] = None
    nombre_verifications: int
    qr_code_data: Optional[str] = None
    chemin_pdf: Optional[str] = None
    evaluation_id: int
    candidature_id: int
    stage_id: int
    entreprise_id: int
    generateur_id: int

    class Config:
        from_attributes = True

class CertificatPublic(BaseModel):
    """Schéma public pour la vérification des certificats."""
    code_unique: str
    titre_stage: str
    date_debut_stage: datetime
    date_fin_stage: datetime
    duree_stage_jours: int
    note_finale: float
    mention: Optional[str] = None
    nom_stagiaire: str
    prenom_stagiaire: str
    nom_entreprise: str
    secteur_entreprise: str
    date_generation: datetime
    est_valide: bool = True

    class Config:
        from_attributes = True

# ============================================================================
# STATISTIQUES
# ============================================================================

class StatistiquesEvaluation(BaseModel):
    """Statistiques sur les évaluations."""
    nombre_evaluations_total: int
    nombre_evaluations_validees: int
    note_moyenne: Optional[float] = None
    repartition_mentions: dict = {}
    taux_recommandation_embauche: Optional[float] = None

class StatistiquesCritere(BaseModel):
    """Statistiques par critère."""
    critere_nom: str
    note_moyenne: float
    nombre_evaluations: int

# ============================================================================
# RÉPONSES AVEC RELATIONS
# ============================================================================

class EvaluationWithRelations(Evaluation):
    """Évaluation avec informations du stage et du stagiaire."""
    stage: Optional[dict] = None  # Informations basiques du stage
    evaluateur: Optional[dict] = None  # Informations de l'évaluateur

    class Config:
        from_attributes = True

class CertificatWithRelations(Certificat):
    """Certificat avec informations complètes."""
    candidature: Optional[dict] = None
    stage: Optional[dict] = None
    evaluation: Optional[dict] = None

# ============================================================================
# SCHÉMAS DE RECHERCHE/FILTRAGE
# ============================================================================

class EvaluationFilters(BaseModel):
    """Filtres pour la recherche d'évaluations."""
    statut: Optional[StatutEvaluationEnum] = None
    note_min: Optional[float] = Field(None, ge=0, le=10)
    note_max: Optional[float] = Field(None, ge=0, le=10)
    recommande_embauche: Optional[bool] = None
    date_debut: Optional[datetime] = None
    date_fin: Optional[datetime] = None

class CertificatFilters(BaseModel):
    """Filtres pour la recherche de certificats."""
    statut: Optional[StatutCertificatEnum] = None
    mention: Optional[str] = None
    annee: Optional[int] = Field(None, ge=2020, le=2030)
    note_min: Optional[float] = Field(None, ge=0, le=10)
    note_max: Optional[float] = Field(None, ge=0, le=10)

# ============================================================================
# SCHÉMAS DE VERIFICATION QR CODE
# ============================================================================

class VerificationQRCode(BaseModel):
    """Schéma pour vérifier un certificat via QR code."""
    code_unique: str

class ResultatVerification(BaseModel):
    """Résultat de la vérification d'un certificat."""
    valide: bool
    certificat: Optional[CertificatPublic] = None
    message: str


