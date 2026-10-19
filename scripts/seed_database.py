"""
CineMind AI — Database Seeding Script
Populates SQLite/PostgreSQL with movies, ratings, links, reviews, sentiment aggregates,
and model evaluation benchmarks from the processed pipeline artifacts.
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
from datetime import datetime

# Add backend to path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.connection import SessionLocal, engine
from app.database.models import Base, Movie, Rating, Review, MovieSentimentAggregate, ModelEvaluation
from app.database.initialization import init_db
from app.ml.sentiment.classifier import get_sentiment_classifier
from app.ml.sentiment.aggregator import SentimentAggregator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CineMind-DatabaseSeeder")

# High-resolution poster mapping for prominent titles
CURATED_POSTERS = {
    1: "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg", # Toy Story
    2: "https://image.tmdb.org/t/p/w500/vgpXmVaMTviZ38kuG22T8Su9umY.jpg", # Jumanji
    3: "https://image.tmdb.org/t/p/w500/15602.jpg",
    6: "https://image.tmdb.org/t/p/w500/rrBuGu0Pjq7Y2JWxJwbgV8vHj9a.jpg", # Heat
    10: "https://image.tmdb.org/t/p/w500/5c0ovjT41KnYI6crWUXIfI2Ahmm.jpg", # GoldenEye
    50: "https://image.tmdb.org/t/p/w500/bUP4L34sWvhNgnKzB6tZfB2d2e1.jpg", # The Usual Suspects
    110: "https://image.tmdb.org/t/p/w500/or1gBugydmjToAEqDpHTj3X27q9.jpg", # Braveheart
    260: "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg", # Star Wars: A New Hope
    296: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg", # Pulp Fiction
    318: "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg", # Shawshank Redemption
    356: "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg", # Forrest Gump
    480: "https://image.tmdb.org/t/p/w500/oU7Oq2kFAAlGqbU4VoAE36g4hoI.jpg", # Jurassic Park
    527: "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQYR0.jpg", # Schindler's List
    593: "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg", # Silence of the Lambs
    858: "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg", # The Godfather
    1196: "https://image.tmdb.org/t/p/w500/2l05cFWJacyIsTpsqSgH0wQXe4V.jpg", # Empire Strikes Back
    1198: "https://image.tmdb.org/t/p/w500/ceG9VzoRAVGwivFU407W8MKSpDY.jpg", # Raiders of the Lost Ark
    2571: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", # The Matrix
    2959: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", # Fight Club
    58559: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", # The Dark Knight
    79132: "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg", # Inception
    109487: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", # Interstellar
    201773: "https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg"  # Parasite
}


def seed_database(processed_dir: str = "data/processed", max_ratings: int = 110000):
    init_db()
    session = SessionLocal()

    try:
        # Check existing movies
        existing_count = session.query(Movie).count()
        if existing_count > 0:
            logger.info(f"Database already populated with {existing_count} movies. Skipping duplicate insertions.")
            return

        movies_csv = os.path.join(processed_dir, "movies_processed.csv")
        ratings_csv = os.path.join(processed_dir, "ratings_cleaned.csv")
        links_csv = os.path.join(processed_dir, "links_cleaned.csv")
        reviews_csv = os.path.join(processed_dir, "reviews_cleaned.csv")
        eval_json = os.path.join(processed_dir, "evaluation_report.json")

        # 1. Load Links
        links_map = {}
        if os.path.exists(links_csv):
            df_links = pd.read_csv(links_csv)
            for _, row in df_links.iterrows():
                try:
                    mid = int(row["movieId"])
                    imdb = str(row.get("imdbId", "")).replace(".0", "")
                    tmdb = str(row.get("tmdbId", "")).replace(".0", "")
                    links_map[mid] = (imdb, tmdb)
                except Exception:
                    pass

        # 2. Insert Movies
        logger.info("Inserting movies into database...")
        df_movies = pd.read_csv(movies_csv)
        movie_objects = []

        for _, row in df_movies.iterrows():
            mid = int(row["movieId"])
            title = str(row["title"])
            genres = str(row.get("genres", ""))
            year = int(row["year"]) if pd.notnull(row.get("year")) and str(row.get("year")).isdigit() else 0
            overview = str(row.get("overview", "")) if pd.notnull(row.get("overview")) else ""
            tags = str(row.get("tags", "")) if pd.notnull(row.get("tags")) else ""
            avg_rating = float(row.get("avg_rating", 0.0))
            rating_count = int(row.get("rating_count", 0))
            weighted_score = float(row.get("weighted_score", 0.0))

            imdb_id, tmdb_id = links_map.get(mid, ("", ""))
            poster_url = CURATED_POSTERS.get(mid, f"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60")

            m = Movie(
                movie_id=mid,
                title=title,
                genres=genres,
                year=year,
                overview=overview,
                tags=tags,
                avg_rating=avg_rating,
                rating_count=rating_count,
                weighted_score=weighted_score,
                imdb_id=imdb_id,
                tmdb_id=tmdb_id,
                poster_url=poster_url
            )
            movie_objects.append(m)

        session.bulk_save_objects(movie_objects)
        session.commit()
        logger.info(f"Successfully inserted {len(movie_objects)} movies.")

        # 3. Insert Ratings (Batch insert)
        logger.info(f"Inserting ratings into database (up to {max_ratings})...")
        df_ratings = pd.read_csv(ratings_csv)
        if len(df_ratings) > max_ratings:
            df_ratings = df_ratings.iloc[:max_ratings]

        valid_movie_ids = set(df_movies["movieId"].tolist())
        rating_objects = []
        for _, row in df_ratings.iterrows():
            mid = int(row["movieId"])
            if mid in valid_movie_ids:
                rating_objects.append(Rating(
                    user_id=int(row["userId"]),
                    movie_id=mid,
                    rating=float(row["rating"]),
                    timestamp=int(row["timestamp"]) if "timestamp" in row and pd.notnull(row["timestamp"]) else None
                ))

        session.bulk_save_objects(rating_objects)
        session.commit()
        logger.info(f"Successfully inserted {len(rating_objects)} ratings.")

        # 4. Insert Reviews & Sentiment Aggregates
        if os.path.exists(reviews_csv):
            logger.info("Analyzing and inserting reviews with transformer predictions...")
            df_reviews = pd.read_csv(reviews_csv)
            classifier = get_sentiment_classifier()
            rev_dicts = df_reviews.to_dict(orient="records")
            predictions = classifier.predict_batch(rev_dicts)

            review_objects = []
            for pred in predictions:
                mid = int(pred["movieId"])
                if mid in valid_movie_ids:
                    review_objects.append(Review(
                        movie_id=mid,
                        review_id=str(pred.get("reviewId", "")),
                        review_text=str(pred.get("reviewText", "")),
                        ground_truth_sentiment=str(pred.get("groundTruthSentiment", "")),
                        predicted_sentiment=str(pred.get("predicted_sentiment", "")),
                        sentiment_confidence=float(pred.get("sentiment_confidence", 0.0))
                    ))

            session.bulk_save_objects(review_objects)
            session.commit()
            logger.info(f"Inserted {len(review_objects)} reviews.")

            # Compute and persist Sentiment Aggregates
            aggregates = SentimentAggregator.aggregate_all_movies(predictions)
            agg_objects = []
            for mid, agg in aggregates.items():
                if mid in valid_movie_ids:
                    agg_objects.append(MovieSentimentAggregate(
                        movie_id=mid,
                        analyzed_reviews=agg["analyzed_reviews"],
                        positive_count=agg["positive_count"],
                        negative_count=agg["negative_count"],
                        positive_ratio=agg["positive_ratio"],
                        aggregate_sentiment_score=agg["aggregate_sentiment_score"],
                        average_confidence=agg["average_confidence"]
                    ))

            session.bulk_save_objects(agg_objects)
            session.commit()
            logger.info(f"Inserted sentiment aggregates for {len(agg_objects)} movies.")

        # 5. Insert Model Evaluations
        if os.path.exists(eval_json):
            with open(eval_json, "r", encoding="utf-8") as f:
                eval_data = json.load(f)

            eval_objects = []
            k_val = eval_data.get("k_value", 10)
            sample_sz = eval_data.get("sample_size_users", 0)

            for model_key, m_info in eval_data.get("models", {}).items():
                eval_objects.append(ModelEvaluation(
                    model_name=model_key,
                    k_value=k_val,
                    precision_at_k=m_info.get("precision_at_k"),
                    recall_at_k=m_info.get("recall_at_k"),
                    ndcg_at_k=m_info.get("ndcg_at_k"),
                    rmse=m_info.get("rmse"),
                    mae=m_info.get("mae"),
                    sample_size=sample_sz
                ))

            session.bulk_save_objects(eval_objects)
            session.commit()
            logger.info("Inserted model evaluation benchmarks.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error during database seeding: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed CineMind AI Database")
    parser.add_argument("--processed-dir", default="data/processed", help="Path to processed data")
    parser.add_argument("--max-ratings", type=int, default=110000, help="Max ratings to insert (defaults to all)")
    args = parser.parse_args()

    seed_database(args.processed_dir, args.max_ratings)
    logger.info("Database seeding process completed.")


if __name__ == "__main__":
    main()
