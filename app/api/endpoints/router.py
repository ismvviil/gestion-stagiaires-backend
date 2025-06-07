from fastapi import APIRouter
from app.api.endpoints import auth, users,entreprises, offres , candidatures, conversations, messages , stages ,missions , contact , upload,admin, stagiaires
from app.api.endpoints.evaluations import router as evaluations_router

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(entreprises.router, prefix="/entreprises", tags=["entreprises"])
api_router.include_router(offres.router, prefix="/offres", tags=["offres"])
api_router.include_router(candidatures.router, prefix="/candidatures", tags=["candidatures"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])

api_router.include_router(stages.router, prefix="/stages", tags=["stages"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])

api_router.include_router(evaluations_router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])

api_router.include_router(upload.router, prefix="/upload", tags=["upload"])  # ← Ajout

api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

api_router.include_router(stagiaires.router, prefix="/stagiaires", tags=["stagiaires"])


@api_router.get("/health-check")
def health_check():
    return {"status": "ok"}