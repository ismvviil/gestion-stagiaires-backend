# Créez ce fichier: fix_unique_constraint.py
from sqlalchemy import text
from app.core.database import SessionLocal

def fix_unique_constraint():
    """Ajouter la contrainte unique sur raison_social avec gestion d'erreur."""
    
    db = SessionLocal()
    try:
        print("🔧 Correction de la contrainte unique...")
        
        # Vérifier si la contrainte existe déjà
        check_constraint = """
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'entreprise' 
        AND constraint_type = 'UNIQUE' 
        AND constraint_name = 'unique_raison_social';
        """
        
        result = db.execute(text(check_constraint)).fetchone()
        
        if result:
            print("✅ La contrainte unique existe déjà")
        else:
            # Ajouter la contrainte unique
            add_constraint = "ALTER TABLE entreprise ADD CONSTRAINT unique_raison_social UNIQUE (raison_social);"
            db.execute(text(add_constraint))
            db.commit()
            print("✅ Contrainte unique ajoutée avec succès")
        
    except Exception as e:
        print(f"⚠️ Erreur lors de l'ajout de la contrainte: {e}")
        print("ℹ️ Ce n'est pas grave si la contrainte existe déjà")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_unique_constraint()