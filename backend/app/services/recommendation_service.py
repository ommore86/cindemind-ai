"""
CineMind AI — Recommendation Service
Manages recommendation engine lifecycles, memory caching of models,
and serving personalized hybrid and cold-start recommendations.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import Movie, Rating, MovieSentimentAggregate
from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender
from app.ml.recommendation.hybrid_engine import HybridRecommendationEngine

logger = logging.getLogger("CineMind-RecommendationService")


class RecommendationService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RecommendationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.content_rec = ContentBasedRecommender(max_features=5000)
        self.collab_rec = CollaborativeRecommender(n_factors=20)
        self.hybrid_engine = HybridRecommendationEngine(
            content_recommender=self.content_rec,
            collaborative_recommender=self.collab_rec,
            w_content=settings.CONTENT_WEIGHT,
            w_collab=settings.COLLABORATIVE_WEIGHT,
            w_sentiment=settings.SENTIMENT_WEIGHT
        )
        self.is_ready = False
        self._initialized = True

    def initialize_models(self, db: Session):
        """Load data from database or processed artifacts and fit models."""
        if self.is_ready:
            return

        logger.info("Initializing recommendation models from database...")
        # 1. Fetch movies
        movies = db.query(Movie).all()
        if not movies:
            logger.warning("No movies found in database to initialize models.")
            return

        movie_dicts = [
            {
                "movieId": m.movie_id,
                "title": m.title,
                "genres": m.genres,
                "year": m.year,
                "overview": m.overview or "",
                "tags": m.tags or "",
                "avg_rating": m.avg_rating,
                "rating_count": m.rating_count,
                "weighted_score": m.weighted_score,
                "poster_url": m.poster_url or "",
                "content_text": f"{m.title} {m.genres.replace('|', ' ')} {m.tags or ''} {m.overview or ''}".strip()
            }
            for m in movies
        ]
        movies_df = pd.DataFrame(movie_dicts)
        self.content_rec.fit(movies_df)

        # 2. Fetch ratings
        ratings = db.query(Rating.user_id, Rating.movie_id, Rating.rating).all()
        if ratings:
            ratings_df = pd.DataFrame(ratings, columns=["userId", "movieId", "rating"])
            self.collab_rec.fit(ratings_df)

        # 3. Fetch sentiment aggregates
        sentiments = db.query(MovieSentimentAggregate).all()
        sentiment_dict = {}
        for s in sentiments:
            sentiment_dict[s.movie_id] = {
                "movie_id": s.movie_id,
                "analyzed_reviews": s.analyzed_reviews,
                "positive_count": s.positive_count,
                "negative_count": s.negative_count,
                "positive_ratio": s.positive_ratio,
                "aggregate_sentiment_score": s.aggregate_sentiment_score,
                "average_confidence": s.average_confidence,
                "sentiment_available": True
            }
        self.hybrid_engine.set_sentiment_aggregates(sentiment_dict)

        self.is_ready = True
        logger.info("Recommendation service initialized and ready.")

    def get_recommendations_for_user(
        self,
        db: Session,
        user_id: int,
        preferred_genres: Optional[List[str]] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Fetch user ratings and generate hybrid recommendations."""
        self.initialize_models(db)

        # Query user ratings from DB
        db_ratings = db.query(Rating.movie_id, Rating.rating).filter(Rating.user_id == user_id).all()
        user_ratings = [{"movieId": r.movie_id, "rating": r.rating} for r in db_ratings]

        is_cold_start = len(user_ratings) == 0

        items = self.hybrid_engine.recommend(
            user_id=user_id if not is_cold_start else None,
            user_ratings=user_ratings,
            preferred_genres=preferred_genres,
            top_n=top_n,
            exclude_rated=True
        )

        return {
            "user_id": user_id,
            "total_recommendations": len(items),
            "is_cold_start": is_cold_start,
            "preferred_genres": preferred_genres or [],
            "base_weights": {
                "content": settings.CONTENT_WEIGHT,
                "collaborative": settings.COLLABORATIVE_WEIGHT,
                "sentiment": settings.SENTIMENT_WEIGHT
            },
            "items": items,
            "_user_ratings": user_ratings
        }

    def get_guest_recommendations(
        self,
        db: Session,
        preferred_genres: List[str],
        seed_movie_ids: List[int],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Cold-start recommendations for guest users."""
        self.initialize_models(db)

        simulated_ratings = [{"movieId": mid, "rating": 5.0} for mid in seed_movie_ids]

        items = self.hybrid_engine.recommend(
            user_id=None,
            user_ratings=simulated_ratings,
            preferred_genres=preferred_genres,
            top_n=top_n,
            exclude_rated=True
        )

        return {
            "user_id": None,
            "total_recommendations": len(items),
            "is_cold_start": True,
            "preferred_genres": preferred_genres,
            "base_weights": {
                "content": settings.CONTENT_WEIGHT,
                "collaborative": settings.COLLABORATIVE_WEIGHT,
                "sentiment": settings.SENTIMENT_WEIGHT
            },
            "items": items,
            "_user_ratings": simulated_ratings
        }


# Singleton accessor
_rec_service = None

def get_recommendation_service() -> RecommendationService:
    global _rec_service
    if _rec_service is None:
        _rec_service = RecommendationService()
    return _rec_service
