from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.providers import LocalProvider
from app.services.model_registry import (
    INSIGHTFACE_LOCAL_MODEL_ID,
    get_model_definition,
    probe_models_startup,
)
from app.supabase import SupabaseClient
from app.routes import attendance, detection_logs, enroll, identities, labs, models, recognize, system


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings
    app.state.provider = LocalProvider()
    SupabaseClient.get_client()
    if settings.has_insightface_colab_config:
        print("INSIGHTFACE_COLAB_URL is deprecated. EntryLens now prefers backend-local model execution.")
    if settings.insightface_startup_probe:
        for model_id, health in probe_models_startup().items():
            print(f"Model startup probe [{model_id}]: {health.status} - {health.detail or 'no detail'}")
    try:
        app.state.models = [
            model.model_dump() for model in [get_model_definition("local-default"), get_model_definition(INSIGHTFACE_LOCAL_MODEL_ID)]
        ]
    except Exception:
        app.state.models = []
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(system.router)
app.include_router(attendance.router)
app.include_router(labs.router, prefix="/api/v1/labs")
app.include_router(models.router, prefix="/api/v1")
app.include_router(enroll.router, prefix="/api/v1")
app.include_router(identities.router, prefix="/api/v1")
app.include_router(recognize.router, prefix="/api/v1")
app.include_router(detection_logs.router, prefix="/api/v1")
