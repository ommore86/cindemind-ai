"""
CineMind AI — Sentiment Pydantic Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ReviewItem(BaseModel):
    id: int
    movie_id: int
    review_id: Optional[str] = ""
    review_text: str
    ground_truth_sentiment: Optional[str] = None
    predicted_sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None


class MovieSentimentSummary(BaseModel):
    movie_id: int
    title: Optional[str] = None
    sentiment_available: bool
    analyzed_reviews: int = 0
    positive_count: int = 0
    negative_count: int = 0
    positive_ratio: float = 0.0
    negative_ratio: float = 0.0
    aggregate_sentiment_score: Optional[float] = None
    average_confidence: float = 0.0
    recent_reviews: List[ReviewItem] = []


class SentimentAnalysisRequest(BaseModel):
    movie_id: Optional[int] = None
    text: str = Field(..., min_length=1, description="Movie review text to analyze")


class SentimentAnalysisResponse(BaseModel):
    text: str
    label: str # POSITIVE or NEGATIVE
    confidence: float
    is_empty: bool
