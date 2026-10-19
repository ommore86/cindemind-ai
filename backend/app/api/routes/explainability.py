"""
CineMind AI — Explainable AI (XAI) Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.explainability_service import get_explainability_service
from app.schemas.explainability import ExplanationResponse

router = APIRouter(prefix="/recommendations", tags=["Explainability"])


@router.get("/{user_id}/{movie_id}/explanation", response_model=ExplanationResponse)
def get_recommendation_explanation(
    user_id: int,
    movie_id: int,
    genre: Optional[str] = Query(None, description="Preferred genres"),
    db: Session = Depends(get_db)
):
    explain_service = get_explainability_service()
    preferred_genres = [g.strip() for g in genre.split(",") if g.strip()] if genre else []

    try:
        explanation = explain_service.explain(
            db=db,
            movie_id=movie_id,
            user_id=user_id,
            preferred_genres=preferred_genres
        )
        return ExplanationResponse(**explanation)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate explanation: {str(e)}"
        )
