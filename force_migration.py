# Créez ce fichier: force_migration.py
from sqlalchemy import text
from app.core.database import SessionLocal

def force_migration():
    """Migration forcée avec vérification individuelle."""
    
    db = SessionLocal()
    try:
        print("🔄 Migration forcée...")
        
        # Définir les migrations une par une
        migrations = [
            ("adresse", "ALTER TABLE entreprise ADD COLUMN adresse VARCHAR;"),
            ("ville", "ALTER TABLE entreprise ADD COLUMN ville VARCHAR;"),
            ("code_postal", "ALTER TABLE entreprise ADD COLUMN code_postal VARCHAR;"),
            ("pays", "ALTER TABLE entreprise ADD COLUMN pays VARCHAR DEFAULT 'France';"),
            ("telephone", "ALTER TABLE entreprise ADD COLUMN telephone VARCHAR;"),
            ("site_web", "ALTER TABLE entreprise ADD COLUMN site_web VARCHAR;"),
            ("taille_entreprise", "ALTER TABLE entreprise ADD COLUMN taille_entreprise VARCHAR;")
        ]
        
        for column_name, migration_sql in migrations:
            try:
                # Vérifier si la colonne existe
                check_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'entreprise' 
                AND column_name = :column_name;
                """
                
                result = db.execute(text(check_sql), {"column_name": column_name}).fetchone()
                
                if result:
                    print(f"✅ {column_name} existe déjà")
                else:
                    # Ajouter la colonne
                    db.execute(text(migration_sql))
                    print(f"✅ {column_name} ajoutée")
                
            except Exception as e:
                print(f"⚠️ Erreur pour {column_name}: {e}")
        
        # Ajouter l'index
        try:
            index_sql = "CREATE INDEX IF NOT EXISTS idx_entreprise_raison_social ON entreprise(raison_social);"
            db.execute(text(index_sql))
            print("✅ Index ajouté")
        except Exception as e:
            print(f"⚠️ Erreur index: {e}")
        
        db.commit()
        print("🎉 Migration terminée!")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    force_migration()