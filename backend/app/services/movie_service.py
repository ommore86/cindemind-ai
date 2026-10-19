"""
CineMind AI — Movie Service
Handles querying, filtering, pagination, and detail retrieval for movies.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.database.models import Movie, Review, MovieSentimentAggregate


class MovieService:
    @staticmethod
    def list_movies(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        genre: Optional[str] = None,
        sort_by: str = "weighted_score",
        order: str = "desc"
    ) -> Tuple[int, List[Movie]]:
        query = db.query(Movie)

        if search:
            query = query.filter(Movie.title.ilike(f"%{search}%"))

        if genre and genre.lower() != "all":
            query = query.filter(Movie.genres.ilike(f"%{genre}%"))

        # Sort
        sort_col = getattr(Movie, sort_by, Movie.weighted_score)
        if order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        total = query.count()
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return total, items

    @staticmethod
    def get_movie_by_id(db: Session, movie_id: int) -> Optional[Movie]:
        return db.query(Movie).filter(Movie.movie_id == movie_id).first()
