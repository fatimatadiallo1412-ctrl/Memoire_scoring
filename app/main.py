from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth
from app.routers import auth, clients
from app.routers import auth, clients, demandes
from app.routers import auth, clients, decisions, demandes
from app.routers import auth, clients, demandes, decisions, parametres,credits
app = FastAPI(
    title="Plateforme de scoring de crédit - microfinance",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # l'interface React
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/sante")
def sante():
    return {"statut": "ok"}

...
app.include_router(clients.router)
...
app.include_router(demandes.router)
app.include_router(decisions.router)
...
app.include_router(parametres.router)
app.include_router(credits.router)