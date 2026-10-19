"""
CineMind AI — Sentiment Service
Manages movie review sentiment analysis, real-time inference, and aggregations.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import Movie, Review, MovieSentimentAggregate
from app.ml.sentiment.classifier import get_sentiment_classifier
from app.ml.sentiment.aggregator import SentimentAggregator


class SentimentService:
    @staticmethod
    def get_movie_sentiment(db: Session, movie_id: int) -> Dict[str, Any]:
        """Fetch movie sentiment summary and reviews."""
        movie = db.query(Movie).filter(Movie.movie_id == movie_id).first()
        if not movie:
            return {"sentiment_available": False, "movie_id": movie_id}

        agg = db.query(MovieSentimentAggregate).filter(MovieSentimentAggregate.movie_id == movie_id).first()
        reviews = db.query(Review).filter(Review.movie_id == movie_id).order_by(Review.id.desc()).limit(10).all()

        if not agg or agg.analyzed_reviews == 0:
            return {
                "movie_id": movie_id,
                "title": movie.title,
                "sentiment_available": False,
                "analyzed_reviews": 0,
                "positive_count": 0,
                "negative_count": 0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "aggregate_sentiment_score": None,
                "average_confidence": 0.0,
                "recent_reviews": [
                    {
                        "id": r.id,
                        "movie_id": r.movie_id,
                        "review_id": r.review_id,
                        "review_text": r.review_text,
                        "ground_truth_sentiment": r.ground_truth_sentiment,
                        "predicted_sentiment": r.predicted_sentiment,
                        "sentiment_confidence": r.sentiment_confidence
                    }
                    for r in reviews
                ]
            }

        return {
            "movie_id": movie_id,
            "title": movie.title,
            "sentiment_available": True,
            "analyzed_reviews": agg.analyzed_reviews,
            "positive_count": agg.positive_count,
            "negative_count": agg.negative_count,
            "positive_ratio": agg.positive_ratio,
            "negative_ratio": round(1.0 - agg.positive_ratio, 4),
            "aggregate_sentiment_score": agg.aggregate_sentiment_score,
            "average_confidence": agg.average_confidence,
            "recent_reviews": [
                {
                    "id": r.id,
                    "movie_id": r.movie_id,
                    "review_id": r.review_id,
                    "review_text": r.review_text,
                    "ground_truth_sentiment": r.ground_truth_sentiment,
                    "predicted_sentiment": r.predicted_sentiment,
                    "sentiment_confidence": r.sentiment_confidence
                }
                for r in reviews
            ]
        }

    @staticmethod
    def analyze_review_text(db: Session, text: str, movie_id: Optional[int] = None) -> Dict[str, Any]:
        """Perform on-the-fly sentiment classification on review text using cached transformer."""
        classifier = get_sentiment_classifier()
        prediction = classifier.predict_one(text)

        # If movie_id is provided, optionally save review to database and update aggregate
        if movie_id:
            rev = Review(
                movie_id=movie_id,
                review_id=f"user_{int(hash(text) % 1000000)}",
                review_text=text,
                predicted_sentiment=prediction["label"],
                sentiment_confidence=prediction["confidence"]
            )
            db.add(rev)
            db.commit()

            # Re-compute aggregate
            all_reviews = db.query(Review).filter(Review.movie_id == movie_id).all()
            rev_dicts = [
                {
                    "movieId": r.movie_id,
                    "predicted_sentiment": r.predicted_sentiment,
                    "sentiment_confidence": r.sentiment_confidence,
                    "is_empty": False
                }
                for r in all_reviews
            ]
            new_agg = SentimentAggregator.aggregate_for_movie(movie_id, rev_dicts)
            if new_agg:
                db_agg = db.query(MovieSentimentAggregate).filter(MovieSentimentAggregate.movie_id == movie_id).first()
                if not db_agg:
                    db_agg = MovieSentimentAggregate(movie_id=movie_id)
                    db.add(db_agg)
                db_agg.analyzed_reviews = new_agg["analyzed_reviews"]
                db_agg.positive_count = new_agg["positive_count"]
                db_agg.negative_count = new_agg["negative_count"]
                db_agg.positive_ratio = new_agg["positive_ratio"]
                db_agg.aggregate_sentiment_score = new_agg["aggregate_sentiment_score"]
                db_agg.average_confidence = new_agg["average_confidence"]
                db.commit()

        return {
            "text": text,
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "is_empty": prediction.get("is_empty", False)
        }
