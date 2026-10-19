"""
CineMind AI — Explainable AI (XAI) Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class SimilarMovieWatched(BaseModel):
    movie_id: int
    title: str
    similarity_score: float
    user_rating: Optional[float] = None


class SentimentEvidence(BaseModel):
    analyzed_reviews: int
    positive_count: int
    negative_count: int
    positive_ratio: float
    average_confidence: float
    sample_quote: Optional[str] = None


class ExplanationResponse(BaseModel):
    movie_id: int
    title: str
    genres: List[str]
    final_score: float
    scores: Dict[str, Optional[float]]
    effective_weights: Dict[str, float]
    matching_genres: List[str]
    shared_keywords: List[str] = []
    similar_movies_watched: List[SimilarMovieWatched] = []
    sentiment_evidence: Optional[SentimentEvidence] = None
    data_coverage: Dict[str, bool]
    user_context: Dict[str, Any]
    natural_language_explanation: str
