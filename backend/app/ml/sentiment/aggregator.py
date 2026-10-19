"""
CineMind AI — Movie Sentiment Aggregator
Aggregates individual review sentiment classifications into movie-level sentiment statistics.
Ensures movies without reviews return explicit unavailable sentiment rather than default neutral/positive.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger("CineMind-SentimentAggregator")


class SentimentAggregator:
    """
    Computes movie-level sentiment statistics and scores.

    Aggregation Formula:
    --------------------
    For a movie m with N analyzed reviews {r_1, ..., r_N}, each with label L_i in {+1 (POSITIVE), -1 (NEGATIVE)}
    and confidence C_i in [0.5, 1.0]:
        1. positive_count = count(L_i == POSITIVE)
        2. negative_count = count(L_i == NEGATIVE)
        3. positive_ratio = positive_count / N
        4. average_confidence = sum(C_i) / N
        5. aggregate_sentiment_score = 
           Weighted combination of positive ratio and confidence margin:
           score = positive_ratio * average_confidence + (1 - average_confidence) * 0.5
           Bounded strictly between [0.0, 1.0].
        
    Critical Constraint:
    --------------------
    If N == 0 (no reviews analyzed for movie m), sentiment is explicitly UNAVAILABLE (None).
    Never assign a synthetic 0.5 neutral or positive score to unreviewed movies.
    """

    @staticmethod
    def aggregate_for_movie(movie_id: int, review_predictions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Compute sentiment summary for a specific movie.
        Returns None if no valid review predictions exist.
        """
        valid_reviews = [
            r for r in review_predictions
            if r.get("movieId") == movie_id and not r.get("is_empty", False)
        ]
        
        if not valid_reviews:
            return None

        n = len(valid_reviews)
        pos_count = sum(1 for r in valid_reviews if r.get("predicted_sentiment") == "POSITIVE")
        neg_count = sum(1 for r in valid_reviews if r.get("predicted_sentiment") == "NEGATIVE")
        
        confidences = [float(r.get("sentiment_confidence", 0.7)) for r in valid_reviews]
        avg_confidence = float(np.mean(confidences))
        pos_ratio = float(pos_count / n)
        
        # Bayesian shrinkage toward 0.5 for small sample sizes
        # score = (pos_count + 1) / (n + 2) adjusted by confidence
        base_ratio = (pos_count + 1.0) / (n + 2.0)
        aggregate_score = round(base_ratio * avg_confidence + 0.5 * (1.0 - avg_confidence), 4)
        aggregate_score = max(0.0, min(1.0, aggregate_score))

        return {
            "movie_id": movie_id,
            "analyzed_reviews": n,
            "positive_count": pos_count,
            "negative_count": neg_count,
            "positive_ratio": round(pos_ratio, 4),
            "negative_ratio": round(neg_count / n, 4),
            "average_confidence": round(avg_confidence, 4),
            "aggregate_sentiment_score": aggregate_score,
            "sentiment_available": True
        }

    @staticmethod
    def aggregate_all_movies(review_predictions: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Aggregate predictions for all movies in the batch.
        Returns a dictionary mapping movieId -> sentiment summary dict.
        """
        grouped = {}
        for r in review_predictions:
            mid = r.get("movieId")
            if mid is not None:
                grouped.setdefault(mid, []).append(r)

        results = {}
        for mid, revs in grouped.items():
            agg = SentimentAggregator.aggregate_for_movie(mid, revs)
            if agg is not None:
                results[mid] = agg

        logger.info(f"Aggregated review sentiment for {len(results)} movies.")
        return results
