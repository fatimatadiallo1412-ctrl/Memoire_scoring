from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import assistant, auth, clients, credits, decisions, demandes, moi, parametres, rapports, referentiels, professions
from app.routers import comptes, contact, reinitialisations, tableau_bord  # noqa: E402

app = FastAPI(
    title="Plateforme de scoring de crédit - microfinance",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # l'interface React
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],    # React doit lire le nom du fichier téléchargé
)


@app.get("/sante")
def sante():
    return {"statut": "ok"}


app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(demandes.router)
app.include_router(decisions.router)
app.include_router(parametres.router)
app.include_router(credits.router)
app.include_router(moi.router)
app.include_router(rapports.router)
app.include_router(assistant.router)
app.include_router(referentiels.router)
app.include_router(professions.router)
app.include_router(contact.router)
app.include_router(tableau_bord.router)
app.include_router(comptes.router)
app.include_router(comptes.router_mdp)
app.include_router(reinitialisations.router)