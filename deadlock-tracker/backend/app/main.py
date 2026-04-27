from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import players, matches, search

app = FastAPI(title="Deadlock Tracker API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(matches.router)
app.include_router(search.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
