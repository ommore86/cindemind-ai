"""
CineMind AI — Hybrid Recommendation Engine
Blends Content-Based, Collaborative Filtering, and Review Sentiment signals.
Features dynamic weight renormalization and honest missing-component policies.
"""

import logging
from typing import List, Dict, Any, Optional, Set
import numpy as np
import pandas as pd
from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender

logger = logging.getLogger("CineMind-HybridEngine")


class HybridRecommendationEngine:
    """
    Hybrid Recommender combining Content-Based, Collaborative, and Sentiment signals.

    Dynamic Normalization Rule:
    ---------------------------
    Given base weights:
        w_cont (e.g. 0.45), w_collab (e.g. 0.40), w_sent (e.g. 0.15)
    For each candidate movie m:
        Active set A = {c in {cont, collab, sent} | c is available for (u, m)}
        If A != empty:
            w'_c = w_c / sum_{i in A} w_i
        Final Score = sum_{c in A} w'_c * S_c
    """

    def __init__(
        self,
        content_recommender: ContentBasedRecommender,
        collaborative_recommender: CollaborativeRecommender,
        w_content: float = 0.45,
        w_collab: float = 0.40,
        w_sentiment: float = 0.15
    ):
        self.content_rec = content_recommender
        self.collab_rec = collaborative_recommender
        
        # Validate weights
        total = w_content + w_collab + w_sentiment
        if total <= 0:
            raise ValueError("Sum of hybrid weights must be positive")
        self.w_content = w_content / total
        self.w_collab = w_collab / total
        self.w_sentiment = w_sentiment / total
        
        self.sentiment_map: Dict[int, Dict[str, Any]] = {}

    def set_sentiment_aggregates(self, sentiment_dict: Dict[int, Dict[str, Any]]):
        """Update cached movie sentiment aggregates."""
        self.sentiment_map = sentiment_dict
        logger.info(f"Loaded sentiment data for {len(sentiment_dict)} movies into hybrid engine.")

    def recommend(
        self,
        user_id: Optional[int],
        user_ratings: List[Dict[str, Any]],
        preferred_genres: Optional[List[str]] = None,
        top_n: int = 10,
        candidate_movies_df: Optional[pd.DataFrame] = None,
        exclude_rated: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate ranked hybrid recommendations with transparent score decomposition.
        """
        rated_mids = {int(r["movieId"]) for r in user_ratings if "movieId" in r}
        
        # 1. Determine candidate movies
        if candidate_movies_df is None:
            if self.content_rec.movie_df is not None:
                candidates = self.content_rec.movie_df
            else:
                return []
        else:
            candidates = candidate_movies_df

        if exclude_rated and rated_mids:
            candidates = candidates[~candidates["movieId"].isin(rated_mids)]

        # Apply genre filter if explicitly specified
        if preferred_genres:
            def matches_genres(genre_str):
                g_lower = str(genre_str).lower()
                return any(pg.lower() in g_lower for pg in preferred_genres)
            candidates = candidates[candidates["genres"].apply(matches_genres)]

        if candidates.empty:
            logger.warning("No candidate movies remaining after filters.")
            return []

        # 2. Score candidates across available channels
        # Get content similarities
        content_results = self.content_rec.recommend_for_user(
            user_ratings=user_ratings,
            preferred_genres=preferred_genres,
            top_n=len(candidates),
            exclude_rated=exclude_rated
        )
        content_score_map = {item["movie_id"]: item["content_score"] for item in content_results}

        # Check if user is known to collaborative engine
        is_known_user = user_id is not None and user_id in self.collab_rec.user_to_idx

        # Precompute vectorized collaborative scores across candidate items
        collab_score_map: Dict[int, float] = {}
        if is_known_user:
            candidate_mids = set(candidates["movieId"])
            collab_score_map = self.collab_rec.predict_user_scores_normalized(user_id, candidate_mids)

        scored_items = []

        for _, row in candidates.iterrows():
            mid = int(row["movieId"])
            title = str(row.get("title", ""))
            genres = str(row.get("genres", ""))
            year = int(row.get("year", 0))
            poster_url = str(row.get("poster_url", ""))
            avg_rating = float(row.get("avg_rating", 0.0))
            rating_count = int(row.get("rating_count", 0))

            # Channel 1: Content Score
            c_score = content_score_map.get(mid, 0.0)
            c_available = True

            # Channel 2: Collaborative Score
            collab_score = collab_score_map.get(mid)
            collab_available = collab_score is not None

            # Channel 3: Sentiment Score
            sentiment_score = None
            sentiment_available = False
            sentiment_meta = self.sentiment_map.get(mid)
            if sentiment_meta and sentiment_meta.get("sentiment_available"):
                sentiment_score = sentiment_meta.get("aggregate_sentiment_score")
                sentiment_available = True

            # Channel 4: Dynamic Weight Renormalization
            active_weights = {}
            if c_available:
                active_weights["content"] = self.w_content
            if collab_available:
                active_weights["collaborative"] = self.w_collab
            if sentiment_available:
                active_weights["sentiment"] = self.w_sentiment

            total_active_w = sum(active_weights.values())
            if total_active_w > 0:
                normalized_weights = {k: v / total_active_w for k, v in active_weights.items()}
            else:
                normalized_weights = {"content": 1.0}

            final_score = 0.0
            if "content" in normalized_weights:
                final_score += normalized_weights["content"] * c_score
            if "collaborative" in normalized_weights and collab_score is not None:
                final_score += normalized_weights["collaborative"] * collab_score
            if "sentiment" in normalized_weights and sentiment_score is not None:
                final_score += normalized_weights["sentiment"] * sentiment_score

            scored_items.append({
                "movie_id": mid,
                "title": title,
                "genres": genres,
                "year": year,
                "poster_url": poster_url,
                "avg_rating": avg_rating,
                "rating_count": rating_count,
                "final_score": round(final_score, 4),
                "content_score": round(c_score, 4),
                "collaborative_score": round(collab_score, 4) if collab_available and collab_score is not None else None,
                "sentiment_score": round(sentiment_score, 4) if sentiment_available and sentiment_score is not None else None,
                "content_available": c_available,
                "collaborative_available": collab_available,
                "sentiment_available": sentiment_available,
                "effective_weights": {k: round(v, 4) for k, v in normalized_weights.items()},
                "is_cold_start": not is_known_user or len(user_ratings) == 0,
                "sentiment_details": sentiment_meta if sentiment_available else None
            })

        # Rank by final score descending
        scored_items.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_items[:top_n]
