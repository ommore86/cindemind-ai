"""
CineMind AI — Movies API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.movie_service import MovieService
from app.schemas.movies import MovieListResponse, MovieDetail, MovieBase

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=MovieListResponse)
def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Title search filter"),
    genre: Optional[str] = Query(None, description="Genre filter"),
    sort_by: str = Query("weighted_score", description="Sort field: weighted_score, avg_rating, year, title"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    db: Session = Depends(get_db)
):
    total, movies = MovieService.list_movies(
        db=db,
        page=page,
        limit=limit,
        search=search,
        genre=genre,
        sort_by=sort_by,
        order=order
    )
    pages = (total + limit - 1) // limit if total > 0 else 1

    items = [
        MovieBase(
            movie_id=m.movie_id,
            title=m.title,
            genres=m.genres,
            year=m.year or 0,
            overview=m.overview or "",
            avg_rating=m.avg_rating or 0.0,
            rating_count=m.rating_count or 0,
            weighted_score=m.weighted_score or 0.0,
            poster_url=m.poster_url or ""
        )
        for m in movies
    ]

    return MovieListResponse(
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        items=items
    )


@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie_detail(
    movie_id: int,
    db: Session = Depends(get_db)
):
    movie = MovieService.get_movie_by_id(db, movie_id)
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found."
        )

    sentiment_score = None
    sentiment_available = False
    review_count = 0

    if movie.sentiment_aggregate and movie.sentiment_aggregate.analyzed_reviews > 0:
        sentiment_score = movie.sentiment_aggregate.aggregate_sentiment_score
        sentiment_available = True
        review_count = movie.sentiment_aggregate.analyzed_reviews
    elif movie.reviews:
        review_count = len(movie.reviews)

    return MovieDetail(
        movie_id=movie.movie_id,
        title=movie.title,
        genres=movie.genres,
        year=movie.year or 0,
        overview=movie.overview or "",
        tags=movie.tags or "",
        avg_rating=movie.avg_rating or 0.0,
        rating_count=movie.rating_count or 0,
        weighted_score=movie.weighted_score or 0.0,
        imdb_id=movie.imdb_id or "",
        tmdb_id=movie.tmdb_id or "",
        poster_url=movie.poster_url or "",
        sentiment_score=sentiment_score,
        sentiment_available=sentiment_available,
        review_count=review_count
    )
