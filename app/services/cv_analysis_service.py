import re
import os
from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2
import docx
from sqlalchemy.orm import Session


class CVAnalysisService:
    """Service simple d'analyse de CV pour extraire les compétences."""

    # Base de données des compétences techniques par catégorie
    COMPETENCES_DATABASE = {
        "langages_programmation": [
            "python", "javascript", "java", "c++", "c#", "php", "ruby", "go", "rust",
            "typescript", "kotlin", "swift", "dart", "scala", "r", "matlab", "sql",
            "html", "css", "xml", "json", "yaml"
        ],
        "frameworks_libraries": [
            "react", "angular", "vue", "node.js", "express", "django", "flask",
            "spring", "laravel", "symfony", "rails", "asp.net", "flutter", 
            "react native", "ionic", "bootstrap", "tailwind", "jquery",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy"
        ],
        "bases_donnees": [
            "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
            "oracle", "sql server", "sqlite", "cassandra", "neo4j"
        ],
        "outils_technologies": [
            "git", "docker", "kubernetes", "jenkins", "gitlab", "github",
            "aws", "azure", "gcp", "linux", "windows", "macos",
            "nginx", "apache", "postman", "swagger", "jira", "trello"
        ],
        "methodologies": [
            "agile", "scrum", "kanban", "devops", "ci/cd", "tdd", "bdd",
            "microservices", "api rest", "soap", "graphql"
        ],
        "soft_skills": [
            "leadership", "communication", "teamwork", "problem solving",
            "creativity", "adaptability", "time management", "project management",
            "analytical thinking", "critical thinking"
        ],
        "langues": [
            "anglais", "français", "espagnol", "allemand", "italien", "arabe",
            "chinois", "japonais", "portugais", "russe"
        ],
        "secteurs": [
            "finance", "banque", "assurance", "e-commerce", "marketing",
            "digital", "web", "mobile", "cybersécurité", "data science",
            "intelligence artificielle", "blockchain", "iot"
        ]
    }

    @classmethod
    def extract_text_from_pdf(cls, file_path: str) -> str:
        """Extraire le texte d'un fichier PDF."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.lower()
        except Exception as e:
            print(f"❌ Erreur extraction PDF: {e}")
            return ""
        
    
    @classmethod
    def extract_text_from_docx(cls, file_path: str) -> str:
        """Extraire le texte d'un fichier DOCX."""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.lower()
        except Exception as e:
            print(f"❌ Erreur extraction DOCX: {e}")
            return ""
        
    @classmethod
    def extract_text_from_cv(cls, file_path: str) -> str:
        """Extraire le texte d'un CV selon son extension."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return cls.extract_text_from_pdf(str(file_path))
        elif extension in ['.docx', '.doc']:
            return cls.extract_text_from_docx(str(file_path))
        else:
            raise ValueError(f"Type de fichier non supporté: {extension}")
        

    @classmethod
    def extract_competences(cls, cv_text: str) -> Dict[str, List[str]]:
        """Extraire les compétences du texte du CV."""
        cv_text_clean = re.sub(r'[^\w\s]', ' ', cv_text.lower())
        cv_words = set(cv_text_clean.split())
        
        competences_found = {}
        
        for category, competences_list in cls.COMPETENCES_DATABASE.items():
            found_in_category = []
            
            for competence in competences_list:
                # Recherche exacte pour les compétences composées
                if ' ' in competence:
                    if competence in cv_text:
                        found_in_category.append(competence)
                else:
                    # Recherche dans les mots individuels
                    if competence in cv_words:
                        found_in_category.append(competence)
            
            if found_in_category:
                competences_found[category] = found_in_category
        
        return competences_found
    

    @classmethod
    def extract_experience_level(cls, cv_text: str) -> str:
        """Estimer le niveau d'expérience basé sur le CV."""
        experience_indicators = {
            "junior": ["stage", "étudiant", "débutant", "junior", "apprenti"],
            "intermediaire": ["2 ans", "3 ans", "expérience", "projet"],
            "senior": ["senior", "lead", "chef", "manager", "expert", "5 ans", "6 ans", "7 ans"],
            "expert": ["architecte", "directeur", "10 ans", "15 ans", "expert"]
        }
        
        scores = {"junior": 0, "intermediaire": 0, "senior": 0, "expert": 0}
        
        for level, indicators in experience_indicators.items():
            for indicator in indicators:
                if indicator in cv_text:
                    scores[level] += 1
        
        # Retourner le niveau avec le plus d'indicateurs
        return max(scores, key=scores.get)
    

    @classmethod
    def analyze_cv_file(cls, file_path: str) -> Dict:
        """Analyser complètement un fichier CV."""
        try:
            print(f"🔍 Analyse du CV: {file_path}")
            
            # Extraire le texte
            cv_text = cls.extract_text_from_cv(file_path)
            
            if not cv_text.strip():
                return {
                    "success": False,
                    "error": "Impossible d'extraire le texte du CV"
                }
            
            # Analyser les compétences
            competences_by_category = cls.extract_competences(cv_text)
            
            # Niveau d'expérience
            experience_level = cls.extract_experience_level(cv_text)
            
            # Compter le total des compétences
            total_competences = sum(len(skills) for skills in competences_by_category.values())
            
            # Créer la liste finale des compétences
            all_competences = []
            for category_skills in competences_by_category.values():
                all_competences.extend(category_skills)
            
            result = {
                "success": True,
                "competences_by_category": competences_by_category,
                "all_competences": all_competences,
                "competences_text": ", ".join(all_competences),
                "total_competences": total_competences,
                "experience_level": experience_level,
                "analysis_summary": {
                    "langages_count": len(competences_by_category.get("langages_programmation", [])),
                    "frameworks_count": len(competences_by_category.get("frameworks_libraries", [])),
                    "tools_count": len(competences_by_category.get("outils_technologies", [])),
                    "soft_skills_count": len(competences_by_category.get("soft_skills", []))
                }
            }
            
            print(f"✅ Analyse terminée: {total_competences} compétences trouvées")
            return result
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
        

    @classmethod
    def update_stagiaire_competences(cls, db: Session, stagiaire_id: int, cv_analysis: Dict):
        """Mettre à jour les compétences extraites du stagiaire."""
        from app.models.stagiaire import Stagiaire
        
        if not cv_analysis.get("success"):
            return False
        
        stagiaire = db.query(Stagiaire).filter(Stagiaire.id == stagiaire_id).first()
        if not stagiaire:
            return False
        
        # Mettre à jour les compétences extraites
        stagiaire.competences_extraites = cv_analysis.get("competences_text", "")
        
        try:
            db.commit()
            print(f"📊 Compétences mises à jour pour stagiaire {stagiaire_id}")
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur mise à jour compétences: {e}")
            return False