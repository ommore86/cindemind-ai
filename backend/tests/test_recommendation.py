"""
Unit Tests for Content-Based, Collaborative Filtering, and Hybrid Recommendation Engine
"""

import pytest
import pandas as pd
import numpy as np

from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender
from app.ml.recommendation.hybrid_engine import HybridRecommendationEngine


@pytest.fixture
def sample_data():
    movies = pd.DataFrame([
        {"movieId": 1, "title": "Toy Story (1995)", "genres": "Animation|Children|Comedy", "year": 1995, "content_text": "Toy Story Animation Children Comedy toys friendship woody buzz", "weighted_score": 4.1, "avg_rating": 4.2, "rating_count": 100},
        {"movieId": 2, "title": "A Bug's Life (1998)", "genres": "Animation|Children|Comedy", "year": 1998, "content_text": "A Bug's Life Animation Children Comedy insects ants pixar", "weighted_score": 3.9, "avg_rating": 3.9, "rating_count": 50},
        {"movieId": 3, "title": "Heat (1995)", "genres": "Action|Crime|Thriller", "year": 1995, "content_text": "Heat Action Crime Thriller heist detective bank robbery pacino deniro", "weighted_score": 4.3, "avg_rating": 4.4, "rating_count": 80},
        {"movieId": 4, "title": "Casino (1995)", "genres": "Crime|Drama", "year": 1995, "content_text": "Casino Crime Drama mafia las vegas mobsters deniro", "weighted_score": 4.2, "avg_rating": 4.3, "rating_count": 75},
        {"movieId": 5, "title": "The Matrix (1999)", "genres": "Action|Sci-Fi", "year": 1999, "content_text": "The Matrix Action Sci-Fi cyberpunk simulated reality neo morpheus", "weighted_score": 4.5, "avg_rating": 4.5, "rating_count": 120},
    ])

    ratings = pd.DataFrame([
        {"userId": 1, "movieId": 1, "rating": 5.0},
        {"userId": 1, "movieId": 2, "rating": 4.5},
        {"userId": 1, "movieId": 3, "rating": 2.0},
        {"userId": 2, "movieId": 3, "rating": 5.0},
        {"userId": 2, "movieId": 4, "rating": 5.0},
        {"userId": 2, "movieId": 1, "rating": 2.0},
        {"userId": 3, "movieId": 5, "rating": 5.0},
        {"userId": 3, "movieId": 3, "rating": 4.0},
    ])

    return movies, ratings


def test_content_based_recommender(sample_data):
    movies_df, _ = sample_data
    cb = ContentBasedRecommender()
    cb.fit(movies_df)

    assert cb.is_fitted
    assert cb.tfidf_matrix.shape[0] == 5

    # Toy Story (1) should be most similar to A Bug's Life (2)
    sims = cb.get_similar_movies(1, top_n=2)
    assert len(sims) > 0
    assert sims[0]["movie_id"] == 2

    # User who likes Animation should get Toy Story & Bug's Life recommended
    user_ratings = [{"movieId": 1, "rating": 5.0}]
    recs = cb.recommend_for_user(user_ratings, top_n=2, exclude_rated=True)
    assert len(recs) > 0
    assert recs[0]["movie_id"] == 2


def test_collaborative_filtering_and_cold_start(sample_data):
    _, ratings_df = sample_data
    cf = CollaborativeRecommender(n_factors=2)
    cf.fit(ratings_df)

    assert cf.is_fitted

    # Known user and movie
    pred, available = cf.predict_rating(user_id=1, movie_id=2)
    assert available
    assert pred is not None
    assert 0.5 <= pred <= 5.0

    # Cold-start unknown user: MUST return available=False
    pred_unknown, avail_unknown = cf.predict_rating(user_id=9999, movie_id=1)
    assert not avail_unknown
    assert pred_unknown is None

    # Cold-start unknown movie: MUST return available=False
    pred_unk_m, avail_unk_m = cf.predict_rating(user_id=1, movie_id=9999)
    assert not avail_unk_m
    assert pred_unk_m is None


def test_hybrid_engine_dynamic_weights_and_missing_sentiment(sample_data):
    movies_df, ratings_df = sample_data
    cb = ContentBasedRecommender()
    cb.fit(movies_df)

    cf = CollaborativeRecommender(n_factors=2)
    cf.fit(ratings_df)

    hybrid = HybridRecommendationEngine(
        content_recommender=cb,
        collaborative_recommender=cf,
        w_content=0.45,
        w_collab=0.40,
        w_sentiment=0.15
    )

    # Supply sentiment only for movie 1 (Toy Story)
    hybrid.set_sentiment_aggregates({
        1: {
            "movie_id": 1,
            "aggregate_sentiment_score": 0.95,
            "sentiment_available": True
        }
    })

    # Test recommendation for User 2 (likes Crime)
    user_ratings = [{"movieId": 3, "rating": 5.0}, {"movieId": 4, "rating": 5.0}]
    results = hybrid.recommend(user_id=2, user_ratings=user_ratings, top_n=3, exclude_rated=True)

    assert len(results) > 0
    for item in results:
        # Check that weights sum strictly to 1.0
        eff_weights = item["effective_weights"]
        assert round(sum(eff_weights.values()), 2) == 1.0

        # For movies without sentiment (e.g. Casino or Matrix), sentiment must NOT be penalized
        if not item["sentiment_available"]:
            assert item["sentiment_score"] is None
            assert "sentiment" not in eff_weights
            # Content & Collaborative must share 100% of the active weights
            assert "content" in eff_weights
            assert "collaborative" in eff_weights

        # Final score must be bounded in [0.0, 1.0]
        assert 0.0 <= item["final_score"] <= 1.0


def test_collaborative_score_normalization_calibrated(sample_data):
    _, ratings_df = sample_data
    cf = CollaborativeRecommender(n_factors=2)
    cf.fit(ratings_df)

    # Test single-item score normalization
    score, available = cf.predict_score_normalized(user_id=1, movie_id=2)
    assert available is True
    assert score is not None
    assert 0.0 <= score <= 1.0

    # Test batch user score normalization across candidates
    user_scores = cf.predict_user_scores_normalized(user_id=1, candidate_movie_ids={2, 3, 4, 5})
    assert isinstance(user_scores, dict)
    assert len(user_scores) > 0
    for mid, s in user_scores.items():
        assert 0.0 <= s <= 1.0

    # User 1 rated movie 1 (5.0) and movie 2 (4.5), and rated movie 3 low (2.0)
    # Movie 2 should receive a higher collaborative affinity than movie 3
    if 2 in user_scores and 3 in user_scores:
        assert user_scores[2] >= user_scores[3]

    # Cold-start checks
    unk_score, unk_avail = cf.predict_score_normalized(user_id=9999, movie_id=1)
    assert unk_avail is False
    assert unk_score is None

    empty_scores = cf.predict_user_scores_normalized(user_id=9999)
    assert empty_scores == {}


def test_hybrid_ranking_balances_collaborative_and_content(sample_data):
    movies_df, ratings_df = sample_data
    cb = ContentBasedRecommender()
    cb.fit(movies_df)

    cf = CollaborativeRecommender(n_factors=2)
    cf.fit(ratings_df)

    hybrid = HybridRecommendationEngine(
        content_recommender=cb,
        collaborative_recommender=cf,
        w_content=0.45,
        w_collab=0.40,
        w_sentiment=0.15
    )

    # User 1 rated movie 1 (5.0) and movie 2 (4.5), and movie 3 (2.0)
    # With candidate movie 2 excluded, recommend from remaining candidates {3, 4, 5}
    user_ratings = [{"movieId": 1, "rating": 5.0}, {"movieId": 2, "rating": 4.5}]
    recs = hybrid.recommend(user_id=1, user_ratings=user_ratings, top_n=3, exclude_rated=True)

    assert len(recs) > 0
    top_rec = recs[0]
    assert 0.0 <= top_rec["final_score"] <= 1.0
    assert "collaborative_score" in top_rec
    assert "content_score" in top_rec
    assert top_rec["collaborative_available"] is True

