"""
CineMind AI — Explainability Service
Coordinates structured explanation generation connecting hybrid scores,
user taste profiles, similar watched movies, and sentiment evidence.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.database.models import Movie, Rating, Review, MovieSentimentAggregate
from app.services.recommendation_service import get_recommendation_service
from app.ml.explainability.explainer import RecommendationExplainer


class ExplainabilityService:
    def __init__(self):
        self.explainer = RecommendationExplainer()

    def explain(
        self,
        db: Session,
        movie_id: int,
        user_id: Optional[int] = None,
        preferred_genres: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        rec_service = get_recommendation_service()
        rec_service.initialize_models(db)

        # 1. Fetch Movie
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            raise ValueError(f"Movie with ID {movie_id} not found.")

        # 2. Fetch User Ratings
        user_ratings = []
        if user_id:
            db_ratings = db.query(Rating.movie_id, Rating.rating).filter(Rating.user_id == user_id).all()
            user_ratings = [{"movieId": r.movie_id, "rating": r.rating} for r in db_ratings]

        # 3. Compute Item Hybrid Score for this movie
        # Get content score
        c_sims = rec_service.content_rec.recommend_for_user(
            user_ratings=user_ratings,
            preferred_genres=preferred_genres,
            top_n=50,
            exclude_rated=False
        )
        c_score_map = {item["movie_id"]: item["content_score"] for item in c_sims}
        c_score = c_score_map.get(movie_id, 0.45)

        # Get collaborative score
        collab_score = None
        collab_avail = False
        if user_id and user_id in rec_service.collab_rec.user_to_idx:
            norm_score, available = rec_service.collab_rec.predict_score_normalized(user_id, movie_id)
            if available and norm_score is not None:
                collab_score = norm_score
                collab_avail = True

        # Get sentiment
        sentiment_score = None
        sentiment_avail = False
        sentiment_data = None
        agg = db.query(MovieSentimentAggregate).filter(MovieSentimentAggregate.movie_id == movie_id).first()
        sample_rev = db.query(Review).filter(Review.movie_id == movie_id, Review.predicted_sentiment == "POSITIVE").first()

        if agg and agg.analyzed_reviews > 0:
            sentiment_score = agg.aggregate_sentiment_score
            sentiment_avail = True
            sentiment_data = {
                "analyzed_reviews": agg.analyzed_reviews,
                "positive_count": agg.positive_count,
                "negative_count": agg.negative_count,
                "positive_ratio": agg.positive_ratio,
                "average_confidence": agg.average_confidence,
                "sample_quote": sample_rev.review_text if sample_rev else None
            }

        # Dynamic weight renormalization
        active_w = {}
        active_w["content"] = rec_service.hybrid_engine.w_content
        if collab_avail:
            active_w["collaborative"] = rec_service.hybrid_engine.w_collab
        if sentiment_avail:
            active_w["sentiment"] = rec_service.hybrid_engine.w_sentiment

        total_w = sum(active_w.values())
        norm_weights = {k: v / total_w for k, v in active_w.items()}

        final_score = norm_weights.get("content", 0.0) * c_score
        if "collaborative" in norm_weights and collab_score is not None:
            final_score += norm_weights["collaborative"] * collab_score
        if "sentiment" in norm_weights and sentiment_score is not None:
            final_score += norm_weights["sentiment"] * sentiment_score

        recommendation_item = {
            "movie_id": movie_id,
            "title": movie.title,
            "genres": movie.genres,
            "year": movie.year,
            "final_score": round(final_score, 4),
            "content_score": round(c_score, 4),
            "collaborative_score": round(collab_score, 4) if collab_score is not None else None,
            "sentiment_score": round(sentiment_score, 4) if sentiment_score is not None else None,
            "content_available": True,
            "collaborative_available": collab_avail,
            "sentiment_available": sentiment_avail,
            "effective_weights": {k: round(v, 4) for k, v in norm_weights.items()},
            "is_cold_start": len(user_ratings) == 0 or not collab_avail
        }

        # 4. Find similar movies user watched and rated highly (>= 3.5)
        similar_watched = []
        if user_ratings and rec_service.content_rec.is_fitted:
            similar_to_this = rec_service.content_rec.get_similar_movies(movie_id, top_n=20)
            user_ratings_map = {r["movieId"]: r["rating"] for r in user_ratings if r.get("rating", 0) >= 3.5}
            for sim_m in similar_to_this:
                sim_mid = sim_m["movie_id"]
                if sim_mid in user_ratings_map:
                    similar_watched.append({
                        "movie_id": sim_mid,
                        "title": sim_m["title"],
                        "similarity_score": sim_m["similarity_score"],
                        "user_rating": user_ratings_map[sim_mid]
                    })
                if len(similar_watched) >= 3:
                    break

        # 5. Explainer synthesis
        explanation = self.explainer.explain_recommendation(
            movie_id=movie_id,
            recommendation=recommendation_item,
            user_ratings=user_ratings,
            preferred_genres=preferred_genres,
            similar_movies_watched=similar_watched,
            sentiment_data=sentiment_data
        )

        return explanation


_explain_service = None

def get_explainability_service() -> ExplainabilityService:
    global _explain_service
    if _explain_service is None:
        _explain_service = ExplainabilityService()
    return _explain_service
