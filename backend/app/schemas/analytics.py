"""
CineMind AI — Analytics Pydantic Schemas
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_movies: int
    total_ratings: int
    total_reviews: int
    unique_users: int
    global_average_rating: float
    spark_pipeline_status: str
    spark_engine: str
    last_updated: str


class RatingDistributionItem(BaseModel):
    rating: float
    count: int


class GenreDistributionItem(BaseModel):
    genre: str
    movie_count: int
    average_rating: float


class SentimentAnalyticsResponse(BaseModel):
    total_reviews_analyzed: int
    positive_reviews: int
    negative_reviews: int
    overall_positive_ratio: float
    top_sentiment_movies: List[Dict[str, Any]]
    bottom_sentiment_movies: List[Dict[str, Any]]


class ModelBenchmarkItem(BaseModel):
    model_name: str
    display_name: str
    precision_at_k: Optional[float] = None
    recall_at_k: Optional[float] = None
    ndcg_at_k: Optional[float] = None
    rmse: Optional[float] = None
    mae: Optional[float] = None


class RecommendationAnalyticsResponse(BaseModel):
    k_value: int
    sample_size_users: int
    benchmarks: List[ModelBenchmarkItem]
    notes: List[str]
