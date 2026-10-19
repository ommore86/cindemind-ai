"""
CineMind AI — Recommendations API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.recommendation_service import get_recommendation_service
from app.schemas.recommendations import (
    RecommendationResponse,
    GuestRecommendationRequest,
    RecommendationItem
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{user_id}", response_model=RecommendationResponse)
def get_user_recommendations(
    user_id: int,
    top_n: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    genre: Optional[str] = Query(None, description="Optional genre preference filter (comma-separated for multiple)"),
    db: Session = Depends(get_db)
):
    rec_service = get_recommendation_service()
    preferred_genres = [g.strip() for g in genre.split(",") if g.strip()] if genre else []

    try:
        result = rec_service.get_recommendations_for_user(
            db=db,
            user_id=user_id,
            preferred_genres=preferred_genres,
            top_n=top_n
        )
        return RecommendationResponse(
            user_id=result["user_id"],
            total_recommendations=result["total_recommendations"],
            is_cold_start=result["is_cold_start"],
            preferred_genres=result["preferred_genres"],
            base_weights=result["base_weights"],
            items=[RecommendationItem(**item) for item in result["items"]]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.post("/guest", response_model=RecommendationResponse)
def get_guest_recommendations(
    request: GuestRecommendationRequest,
    db: Session = Depends(get_db)
):
    rec_service = get_recommendation_service()

    try:
        result = rec_service.get_guest_recommendations(
            db=db,
            preferred_genres=request.preferred_genres,
            seed_movie_ids=request.seed_movie_ids,
            top_n=request.top_n
        )
        return RecommendationResponse(
            user_id=result["user_id"],
            total_recommendations=result["total_recommendations"],
            is_cold_start=result["is_cold_start"],
            preferred_genres=result["preferred_genres"],
            base_weights=result["base_weights"],
            items=[RecommendationItem(**item) for item in result["items"]]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate guest recommendations: {str(e)}"
        )
