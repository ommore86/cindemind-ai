"""
CineMind AI — Recommendation Service
Manages recommendation engine lifecycles, memory caching of models,
and serving personalized hybrid and cold-start recommendations.
"""

import os
import logging
import threading
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

        self._lock = threading.Lock()
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
        """Load data from database and fit models with thread-safe locking."""
        if self.is_ready:
            return

        with self._lock:
            if self.is_ready:
                return

            # 1. Attempt to reuse precomputed model artifacts from disk
            import joblib
            model_dir_candidates = [
                os.path.join("data", "processed", "models"),
                os.path.join("..", "data", "processed", "models"),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed", "models")),
            ]
            content_path = None
            collab_path = None
            for mdir in model_dir_candidates:
                c_p = os.path.join(mdir, "content_model.joblib")
                cl_p = os.path.join(mdir, "collab_model.joblib")
                if os.path.exists(c_p) and os.path.exists(cl_p):
                    content_path = c_p
                    collab_path = cl_p
                    break

            # Validate artifact compatibility against database movie count
            try:
                db_movie_count = db.query(Movie.movie_id).count()
            except Exception:
                db_movie_count = 0

            if content_path and collab_path:
                try:
                    logger.info(f"Validating precomputed recommendation artifacts from {os.path.dirname(content_path)}...")
                    content_state = joblib.load(content_path)
                    collab_state = joblib.load(collab_path)

                    artifact_movies = content_state.get("num_movies", 0)
                    is_compatible = (
                        content_state.get("version") == "1.0.0" and
                        collab_state.get("version") == "1.0.0" and
                        (db_movie_count == 0 or artifact_movies == db_movie_count)
                    )

                    if is_compatible:
                        self.content_rec.load_from_dict(content_state)
                        self.collab_rec.load_from_dict(collab_state)

                        # Load sentiment aggregates from DB if present
                        try:
                            sentiments_df = pd.read_sql_query(
                                "SELECT movie_id, analyzed_reviews, positive_count, negative_count, positive_ratio, aggregate_sentiment_score, average_confidence FROM movie_sentiment_aggregates",
                                db.bind
                            )
                            sentiment_dict = {
                                int(row["movie_id"]): {
                                    "movie_id": int(row["movie_id"]),
                                    "analyzed_reviews": int(row["analyzed_reviews"]),
                                    "positive_count": int(row["positive_count"]),
                                    "negative_count": int(row["negative_count"]),
                                    "positive_ratio": float(row["positive_ratio"]),
                                    "aggregate_sentiment_score": float(row["aggregate_sentiment_score"]),
                                    "average_confidence": float(row["average_confidence"]),
                                    "sentiment_available": True
                                }
                                for _, row in sentiments_df.iterrows()
                            }
                        except Exception:
                            sentiment_dict = {}

                        self.hybrid_engine.set_sentiment_aggregates(sentiment_dict)
                        self.is_ready = True
                        logger.info(
                            f"Recommendation models initialized from precomputed artifacts: "
                            f"{artifact_movies} movies, {len(collab_state.get('user_to_idx', {}))} users. Zero training needed."
                        )
                        return
                    else:
                        logger.warning(
                            f"Precomputed artifact mismatch (artifact movies: {artifact_movies}, db movies: {db_movie_count}). "
                            "Retraining models from active database..."
                        )
                except Exception as e:
                    logger.warning(f"Failed loading model artifacts: {e}. Falling back to database fit.")

            # 2. Fit models from database if artifacts are missing or incompatible
            logger.info("Initializing recommendation models from database...")
            # 2a. Fetch movies using optimized SQL query
            try:
                movies_df = pd.read_sql_query(
                    "SELECT movie_id AS movieId, title, genres, year, overview, tags, avg_rating, rating_count, weighted_score, poster_url FROM movies",
                    db.bind
                )
            except Exception as e:
                logger.warning(f"Error querying movies with pandas: {e}, falling back to ORM")
                movies = db.query(Movie).all()
                if not movies:
                    logger.warning("No movies found in database to initialize models.")
                    return
                movies_df = pd.DataFrame([
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
                        "poster_url": m.poster_url or ""
                    }
                    for m in movies
                ])

            if movies_df.empty:
                logger.warning("No movies found in database to initialize models.")
                return

            movies_df["content_text"] = (
                movies_df["title"].fillna("") + " " +
                movies_df["genres"].fillna("").str.replace("|", " ", regex=False) + " " +
                movies_df["tags"].fillna("") + " " +
                movies_df["overview"].fillna("")
            ).str.strip()
            self.content_rec.fit(movies_df)

            # 2b. Fetch ratings using optimized SQL query
            try:
                ratings_df = pd.read_sql_query(
                    "SELECT user_id AS userId, movie_id AS movieId, rating FROM ratings",
                    db.bind
                )
            except Exception:
                ratings = db.query(Rating.user_id, Rating.movie_id, Rating.rating).all()
                ratings_df = pd.DataFrame(ratings, columns=["userId", "movieId", "rating"]) if ratings else pd.DataFrame()

            if not ratings_df.empty:
                self.collab_rec.fit(ratings_df)

            # 2c. Fetch sentiment aggregates
            try:
                sentiments_df = pd.read_sql_query(
                    "SELECT movie_id, analyzed_reviews, positive_count, negative_count, positive_ratio, aggregate_sentiment_score, average_confidence FROM movie_sentiment_aggregates",
                    db.bind
                )
                sentiment_dict = {
                    int(row["movie_id"]): {
                        "movie_id": int(row["movie_id"]),
                        "analyzed_reviews": int(row["analyzed_reviews"]),
                        "positive_count": int(row["positive_count"]),
                        "negative_count": int(row["negative_count"]),
                        "positive_ratio": float(row["positive_ratio"]),
                        "aggregate_sentiment_score": float(row["aggregate_sentiment_score"]),
                        "average_confidence": float(row["average_confidence"]),
                        "sentiment_available": True
                    }
                    for _, row in sentiments_df.iterrows()
                }
            except Exception:
                sentiments = db.query(MovieSentimentAggregate).all()
                sentiment_dict = {
                    s.movie_id: {
                        "movie_id": s.movie_id,
                        "analyzed_reviews": s.analyzed_reviews,
                        "positive_count": s.positive_count,
                        "negative_count": s.negative_count,
                        "positive_ratio": s.positive_ratio,
                        "aggregate_sentiment_score": s.aggregate_sentiment_score,
                        "average_confidence": s.average_confidence,
                        "sentiment_available": True
                    }
                    for s in sentiments
                }
            self.hybrid_engine.set_sentiment_aggregates(sentiment_dict)

            # 2d. Cache precomputed artifacts to disk for future lightweight startups
            try:
                target_dir = model_dir_candidates[2] if os.path.exists(model_dir_candidates[2]) else model_dir_candidates[0]
                os.makedirs(target_dir, exist_ok=True)
                joblib.dump(self.content_rec.to_dict(), os.path.join(target_dir, "content_model.joblib"), compress=3)
                joblib.dump(self.collab_rec.to_dict(), os.path.join(target_dir, "collab_model.joblib"), compress=3)
                logger.info(f"Cached fitted recommendation model artifacts to {target_dir} for instant startup.")
            except Exception as e:
                logger.warning(f"Could not cache model artifacts: {e}")

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
