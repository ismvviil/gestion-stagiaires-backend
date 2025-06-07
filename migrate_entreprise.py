# Créez ce fichier: migrate_entreprise.py à la racine de votre projet
from sqlalchemy import text
from app.core.database import SessionLocal

def migrate_entreprise_table():
    """Ajouter les nouvelles colonnes à la table entreprise."""
    
    db = SessionLocal()
    try:
        print("🔄 Migration de la table entreprise...")
        
        # Ajouter les nouvelles colonnes
        migrations = [
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS adresse VARCHAR;",
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS ville VARCHAR;",
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS code_postal VARCHAR;",
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS pays VARCHAR DEFAULT 'France';",
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS telephone VARCHAR;",
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS site_web VARCHAR;",
            "ALTER TABLE entreprise ADD COLUMN IF NOT EXISTS taille_entreprise VARCHAR;",
            
            # Ajouter un index sur raison_social pour les recherches
            "CREATE INDEX IF NOT EXISTS idx_entreprise_raison_social ON entreprise(raison_social);",
            
            # Ajouter contrainte unique sur raison_social si pas déjà fait
            "ALTER TABLE entreprise ADD CONSTRAINT IF NOT EXISTS unique_raison_social UNIQUE (raison_social);"
        ]
        
        for migration in migrations:
            try:
                db.execute(text(migration))
                print(f"✅ {migration}")
            except Exception as e:
                print(f"⚠️ Migration déjà appliquée ou erreur: {migration} - {e}")
        
        db.commit()
        print("✅ Migration terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur de migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_entreprise_table()