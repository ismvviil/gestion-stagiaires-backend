# clean_reset.py
from app.core.database import engine
from sqlalchemy import text

print("🧹 Nettoyage complet avec CASCADE...")

with engine.connect() as conn:
    try:
        # Supprimer toutes les tables de messagerie avec CASCADE
        conn.execute(text("DROP TABLE IF EXISTS message CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS conversation_participants CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS conversation CASCADE"))
        conn.commit()
        print("✅ Toutes les tables supprimées avec CASCADE")
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")
        conn.rollback()

print("🏗️ Recréation des tables avec la nouvelle structure...")

# Importer les modèles APRÈS la suppression
from app.models.conversation import Conversation
from app.models.message import Message

try:
    # Créer les nouvelles tables
    Conversation.__table__.create(engine, checkfirst=True)
    Message.__table__.create(engine, checkfirst=True)
    print("✅ Tables recréées avec la nouvelle structure !")
    
    # Vérifier la structure
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'conversation'"))
        columns = [row[0] for row in result.fetchall()]
        print(f"📋 Colonnes de la table conversation : {columns}")
        
except Exception as e:
    print(f"❌ Erreur lors de la création : {e}")

print("🎉 Nettoyage terminé !")