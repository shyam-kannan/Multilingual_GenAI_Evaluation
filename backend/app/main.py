from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import golden_sets, health, prompts

app = FastAPI(
    title="Multilingual GenAI Evaluation Gateway",
    description="Evaluate and moderate LLM outputs across multiple languages",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(prompts.router)
app.include_router(golden_sets.router)
