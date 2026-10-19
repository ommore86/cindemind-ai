"""
CineMind AI — Recommendation Pydantic Schemas
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    movie_id: int
    title: str
    genres: str
    year: int = 0
    poster_url: Optional[str] = ""
    avg_rating: float = 0.0
    rating_count: int = 0
    final_score: float
    content_score: Optional[float] = None
    collaborative_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    content_available: bool = True
    collaborative_available: bool = False
    sentiment_available: bool = False
    effective_weights: Dict[str, float] = {}
    is_cold_start: bool = False


class RecommendationResponse(BaseModel):
    user_id: Optional[int]
    total_recommendations: int
    is_cold_start: bool
    preferred_genres: List[str] = []
    base_weights: Dict[str, float]
    items: List[RecommendationItem]


class GuestRecommendationRequest(BaseModel):
    preferred_genres: List[str] = Field(default_factory=list)
    seed_movie_ids: List[int] = Field(default_factory=list)
    top_n: int = Field(default=10, ge=1, le=50)
