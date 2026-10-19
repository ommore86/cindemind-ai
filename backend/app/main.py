"""
CineMind AI — FastAPI Main Application
Big Data Movie Recommendation System with Sentiment Analysis and Explainable AI
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.initialization import init_db
from app.services.recommendation_service import get_recommendation_service
from app.api.routes import movies, recommendations, explainability, sentiment, analytics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CineMind-API")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist
    logger.info("Starting up CineMind AI application...")
    init_db()
    
    # Warm up recommendation models in background thread
    # This allows Uvicorn to immediately bind to $PORT and pass Render's port detection in <1s
    import threading

    def _background_warmup():
        try:
            logger.info("Background model warm-up started...")
            db = SessionLocal()
            from app.database.initialization import auto_seed_if_empty
            auto_seed_if_empty(db)
            rec_service = get_recommendation_service()
            rec_service.initialize_models(db)
            db.close()
            logger.info("Recommendation service pre-warmed successfully in background.")
        except Exception as e:
            logger.warning(f"Could not pre-warm recommendation service in background: {e}")

    threading.Thread(target=_background_warmup, daemon=True, name="CineMind-Warmup").start()

    yield

    # Shutdown
    logger.info("Shutting down CineMind AI application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Big Data Movie Recommendation System with Sentiment Analysis and Explainable AI",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Middleware: Development origins + Deployed frontend URL + Render preview domains
cors_origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_origin_regex=r"https?://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


# Include Routers
app.include_router(movies.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(explainability.router, prefix=settings.API_V1_STR)
app.include_router(sentiment.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
