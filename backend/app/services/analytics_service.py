"""
CineMind AI — Analytics Service
Aggregates big-data dataset statistics, ratings distributions,
genre analytics, sentiment breakdowns, and model benchmarks.
"""

import os
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.config import settings
from app.database.models import Movie, Rating, Review, MovieSentimentAggregate, ModelEvaluation


class AnalyticsService:
    @staticmethod
    def get_overview(db: Session) -> Dict[str, Any]:
        total_movies = db.query(Movie).count()
        total_ratings = db.query(Rating).count()
        total_reviews = db.query(Review).count()
        unique_users = db.query(Rating.user_id).distinct().count()
        global_avg = db.query(func.avg(Rating.rating)).scalar() or 3.5

        # Read spark pipeline report if available
        engine_name = "Apache Spark (PySpark)"
        last_updated = "Recent"
        if os.path.exists(settings.DATA_QUALITY_REPORT_PATH):
            try:
                with open(settings.DATA_QUALITY_REPORT_PATH, "r", encoding="utf-8") as f:
                    q_report = json.load(f)
                    engine_name = q_report.get("engine", engine_name)
                    last_updated = q_report.get("timestamp", last_updated)
            except Exception:
                pass

        return {
            "total_movies": total_movies,
            "total_ratings": total_ratings,
            "total_reviews": total_reviews,
            "unique_users": unique_users,
            "global_average_rating": round(float(global_avg), 2),
            "spark_pipeline_status": "Completed",
            "spark_engine": engine_name,
            "last_updated": last_updated
        }

    @staticmethod
    def get_ratings_distribution(db: Session) -> List[Dict[str, Any]]:
        # Count per rating score [0.5, 1.0, 1.5, ..., 5.0]
        results = db.query(Rating.rating, func.count(Rating.id)).group_by(Rating.rating).order_by(Rating.rating).all()
        return [{"rating": float(r), "count": int(c)} for r, c in results]

    @staticmethod
    def get_genre_distribution(db: Session) -> List[Dict[str, Any]]:
        # Extract individual genres and aggregate counts and avg ratings
        movies = db.query(Movie.genres, Movie.avg_rating).filter(Movie.genres.isnot(None)).all()
        genre_stats = {}
        for g_str, r_avg in movies:
            if not g_str or g_str == "(no genres listed)":
                continue
            for g in g_str.split("|"):
                g = g.strip()
                if not g:
                    continue
                if g not in genre_stats:
                    genre_stats[g] = {"count": 0, "rating_sum": 0.0}
                genre_stats[g]["count"] += 1
                genre_stats[g]["rating_sum"] += (r_avg or 0.0)

        distribution = [
            {
                "genre": g,
                "movie_count": data["count"],
                "average_rating": round(data["rating_sum"] / data["count"], 2) if data["count"] > 0 else 0.0
            }
            for g, data in genre_stats.items()
        ]
        distribution.sort(key=lambda x: x["movie_count"], reverse=True)
        return distribution

    @staticmethod
    def get_sentiment_analytics(db: Session) -> Dict[str, Any]:
        total_revs = db.query(Review).count()
        pos_revs = db.query(Review).filter(Review.predicted_sentiment == "POSITIVE").count()
        neg_revs = db.query(Review).filter(Review.predicted_sentiment == "NEGATIVE").count()
        overall_ratio = round(pos_revs / total_revs, 4) if total_revs > 0 else 0.0

        # Top sentiment movies
        top_movies_q = (
            db.query(Movie.movie_id, Movie.title, Movie.poster_url, MovieSentimentAggregate.aggregate_sentiment_score, MovieSentimentAggregate.analyzed_reviews)
            .join(MovieSentimentAggregate, Movie.movie_id == MovieSentimentAggregate.movie_id)
            .filter(MovieSentimentAggregate.analyzed_reviews >= 2)
            .order_by(MovieSentimentAggregate.aggregate_sentiment_score.desc())
            .limit(5)
            .all()
        )

        top_movies = [
            {
                "movie_id": m[0],
                "title": m[1],
                "poster_url": m[2],
                "sentiment_score": m[3],
                "reviews_count": m[4]
            }
            for m in top_movies_q
        ]

        # Bottom / polarizing sentiment movies
        bottom_movies_q = (
            db.query(Movie.movie_id, Movie.title, Movie.poster_url, MovieSentimentAggregate.aggregate_sentiment_score, MovieSentimentAggregate.analyzed_reviews)
            .join(MovieSentimentAggregate, Movie.movie_id == MovieSentimentAggregate.movie_id)
            .filter(MovieSentimentAggregate.analyzed_reviews >= 2)
            .order_by(MovieSentimentAggregate.aggregate_sentiment_score.asc())
            .limit(5)
            .all()
        )

        bottom_movies = [
            {
                "movie_id": m[0],
                "title": m[1],
                "poster_url": m[2],
                "sentiment_score": m[3],
                "reviews_count": m[4]
            }
            for m in bottom_movies_q
        ]

        return {
            "total_reviews_analyzed": total_revs,
            "positive_reviews": pos_revs,
            "negative_reviews": neg_revs,
            "overall_positive_ratio": overall_ratio,
            "top_sentiment_movies": top_movies,
            "bottom_sentiment_movies": bottom_movies
        }

    @staticmethod
    def get_recommendation_benchmarks(db: Session) -> Dict[str, Any]:
        # Try database first
        evals = db.query(ModelEvaluation).all()
        display_names = {
            "content_based": "Content-Based Filtering (TF-IDF + Cosine)",
            "collaborative": "Collaborative Filtering (Truncated SVD Matrix Factorization)",
            "hybrid": "Hybrid Engine (Content + Collaborative + Sentiment)"
        }

        benchmarks = []
        k_val = 10
        sample_sz = 50

        if evals:
            for ev in evals:
                k_val = ev.k_value or 10
                sample_sz = ev.sample_size or 50
                benchmarks.append({
                    "model_name": ev.model_name,
                    "display_name": display_names.get(ev.model_name, ev.model_name.capitalize()),
                    "precision_at_k": ev.precision_at_k,
                    "recall_at_k": ev.recall_at_k,
                    "ndcg_at_k": ev.ndcg_at_k,
                    "rmse": ev.rmse,
                    "mae": ev.mae
                })
        elif os.path.exists(settings.EVALUATION_REPORT_PATH):
            with open(settings.EVALUATION_REPORT_PATH, "r", encoding="utf-8") as f:
                rep = json.load(f)
                k_val = rep.get("k_value", 10)
                sample_sz = rep.get("sample_size_users", 50)
                for m_key, m_info in rep.get("models", {}).items():
                    benchmarks.append({
                        "model_name": m_key,
                        "display_name": m_info.get("name", m_key),
                        "precision_at_k": m_info.get("precision_at_k"),
                        "recall_at_k": m_info.get("recall_at_k"),
                        "ndcg_at_k": m_info.get("ndcg_at_k"),
                        "rmse": m_info.get("rmse"),
                        "mae": m_info.get("mae")
                    })

        return {
            "k_value": k_val,
            "sample_size_users": sample_sz,
            "benchmarks": benchmarks,
            "notes": [
                "Evaluated using a 80/20 stratified user rating train/test split.",
                "Relevant items defined as test ratings with rating >= 3.5.",
                "RMSE and MAE are only applicable to Collaborative Filtering which directly predicts explicit star ratings.",
                "Hybrid recommender balances personalization, catalog discovery, and positive sentiment evidence."
            ]
        }
