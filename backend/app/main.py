from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import ci, dashboard, eval_runs, gateway, golden_sets, health, prompts


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url.startswith("sqlite"):
        from app.database import Base, engine
        import app.models.prompt
        import app.models.golden_set
        import app.models.eval_run
        import app.models.ci_run
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Multilingual GenAI Evaluation Gateway",
    description="Evaluate and moderate LLM outputs across multiple languages",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(gateway.router)
app.include_router(eval_runs.router)
app.include_router(ci.router)
app.include_router(dashboard.router)
