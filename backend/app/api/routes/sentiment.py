"""
CineMind AI — Sentiment Analysis API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.sentiment_service import SentimentService
from app.schemas.sentiment import (
    MovieSentimentSummary,
    SentimentAnalysisRequest,
    SentimentAnalysisResponse
)

router = APIRouter(prefix="", tags=["Sentiment"])


@router.get("/movies/{movie_id}/sentiment", response_model=MovieSentimentSummary)
def get_movie_sentiment(
    movie_id: int,
    db: Session = Depends(get_db)
):
    result = SentimentService.get_movie_sentiment(db, movie_id)
    return MovieSentimentSummary(**result)


@router.post("/sentiment/analyze", response_model=SentimentAnalysisResponse)
def analyze_review_text(
    payload: SentimentAnalysisRequest,
    db: Session = Depends(get_db)
):
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review text cannot be empty."
        )

    res = SentimentService.analyze_review_text(db, payload.text, payload.movie_id)
    return SentimentAnalysisResponse(**res)
