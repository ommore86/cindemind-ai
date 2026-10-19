"""
CineMind AI — Movie Pydantic Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MovieBase(BaseModel):
    movie_id: int
    title: str
    genres: str
    year: Optional[int] = 0
    overview: Optional[str] = ""
    avg_rating: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    weighted_score: Optional[float] = 0.0
    poster_url: Optional[str] = ""


class MovieDetail(MovieBase):
    tags: Optional[str] = ""
    imdb_id: Optional[str] = ""
    tmdb_id: Optional[str] = ""
    sentiment_score: Optional[float] = None
    sentiment_available: bool = False
    review_count: int = 0


class MovieListResponse(BaseModel):
    total: int
    page: int
    limit: int
    pages: int
    items: List[MovieBase]
