"""
CineMind AI — Analytics API Endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    AnalyticsOverview,
    RatingDistributionItem,
    GenreDistributionItem,
    SentimentAnalyticsResponse,
    RecommendationAnalyticsResponse,
    ModelBenchmarkItem
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(db: Session = Depends(get_db)):
    data = AnalyticsService.get_overview(db)
    return AnalyticsOverview(**data)


@router.get("/ratings", response_model=List[RatingDistributionItem])
def get_ratings_distribution(db: Session = Depends(get_db)):
    items = AnalyticsService.get_ratings_distribution(db)
    return [RatingDistributionItem(**item) for item in items]


@router.get("/genres", response_model=List[GenreDistributionItem])
def get_genre_distribution(db: Session = Depends(get_db)):
    items = AnalyticsService.get_genre_distribution(db)
    return [GenreDistributionItem(**item) for item in items]


@router.get("/sentiment", response_model=SentimentAnalyticsResponse)
def get_sentiment_analytics(db: Session = Depends(get_db)):
    data = AnalyticsService.get_sentiment_analytics(db)
    return SentimentAnalyticsResponse(**data)


@router.get("/recommendations", response_model=RecommendationAnalyticsResponse)
def get_recommendation_benchmarks(db: Session = Depends(get_db)):
    data = AnalyticsService.get_recommendation_benchmarks(db)
    return RecommendationAnalyticsResponse(
        k_value=data["k_value"],
        sample_size_users=data["sample_size_users"],
        benchmarks=[ModelBenchmarkItem(**b) for b in data["benchmarks"]],
        notes=data["notes"]
    )
