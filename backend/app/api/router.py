from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.analytics import router as analytics_router
from app.api.routes.chat import router as chat_router
from app.api.routes.demo import router as demo_router
from app.api.routes.docs import router as docs_router
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.users import router as users_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(demo_router)
api_router.include_router(docs_router)
api_router.include_router(analytics_router)
api_router.include_router(history_router)
api_router.include_router(chat_router)
api_router.include_router(users_router)
