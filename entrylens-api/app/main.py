from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.providers import LocalProvider
from app.supabase import SupabaseClient
from app.routes import attendance, enroll, identities, labs, recognize, system


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = settings
    app.state.provider = LocalProvider()
    SupabaseClient.get_client()
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
app.include_router(enroll.router, prefix="/api/v1")
app.include_router(identities.router, prefix="/api/v1")
app.include_router(recognize.router, prefix="/api/v1")
