# reset_messaging.py
from app.core.database import engine
from app.models.base import BaseModel
from app.models.conversation import Conversation
from app.models.message import Message

print("🗑️ Suppression des tables de messagerie...")
try:
    # Supprimer seulement les tables de messagerie
    Message.__table__.drop(engine, checkfirst=True)
    Conversation.__table__.drop(engine, checkfirst=True)
    print("✅ Tables supprimées")
except Exception as e:
    print(f"⚠️ Erreur lors de la suppression : {e}")

print("🏗️ Création des nouvelles tables...")
try:
    Conversation.__table__.create(engine, checkfirst=True)
    Message.__table__.create(engine, checkfirst=True)
    print("✅ Tables créées avec succès !")
except Exception as e:
    print(f"❌ Erreur lors de la création : {e}")

print("🎉 Terminé ! Vous pouvez maintenant tester votre API de messagerie.")