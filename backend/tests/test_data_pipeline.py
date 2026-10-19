"""
Unit & Integration Tests for Big Data Pipeline and Cleansing Logic
"""

import os
import pytest
import pandas as pd
from scripts.run_pipeline import run_pipeline_local


def test_pipeline_local_execution(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    # Create dummy raw datasets with intentional anomalies (duplicates, invalid ratings, missing genres)
    movies_df = pd.DataFrame([
        {"movieId": 1, "title": "Toy Story (1995)", "genres": "Animation|Children", "year": 1995, "overview": "Buzz and Woody"},
        {"movieId": 1, "title": "Toy Story Duplicate (1995)", "genres": "Animation", "year": 1995, "overview": "Duplicate"}, # duplicate
        {"movieId": 2, "title": "Jumanji (1995)", "genres": "(no genres listed)", "year": 1995, "overview": "Board game"}, # missing genres
    ])
    movies_df.to_csv(raw_dir / "movies.csv", index=False)

    ratings_df = pd.DataFrame([
        {"userId": 1, "movieId": 1, "rating": 5.0, "timestamp": 100},
        {"userId": 1, "movieId": 1, "rating": 4.5, "timestamp": 200}, # duplicate user rating
        {"userId": 1, "movieId": 2, "rating": 99.0, "timestamp": 300}, # invalid rating out of range
        {"userId": 2, "movieId": 1, "rating": 4.0, "timestamp": 400},
    ])
    ratings_df.to_csv(raw_dir / "ratings.csv", index=False)

    report = run_pipeline_local(str(raw_dir), str(processed_dir))

    assert os.path.exists(processed_dir / "movies_processed.csv")
    assert os.path.exists(processed_dir / "ratings_cleaned.csv")
    assert os.path.exists(processed_dir / "user_profiles.csv")

    cleaned_movies = pd.read_csv(processed_dir / "movies_processed.csv")
    cleaned_ratings = pd.read_csv(processed_dir / "ratings_cleaned.csv")

    # Verify deduplication
    assert len(cleaned_movies) == 2
    # Verify invalid rating filtered (only ratings 0.5 - 5.0 kept) and duplicate rating removed
    assert len(cleaned_ratings) == 2
    assert (cleaned_ratings["rating"] <= 5.0).all()
    assert (cleaned_ratings["rating"] >= 0.5).all()

    # Verify Bayesian weighted score exists
    assert "weighted_score" in cleaned_movies.columns
    assert "content_text" in cleaned_movies.columns
