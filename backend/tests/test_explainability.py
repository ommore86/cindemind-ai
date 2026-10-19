"""
Unit Tests for Explainable AI (XAI) Attribution Engine
"""

import pytest
from app.ml.explainability.explainer import RecommendationExplainer


def test_explainable_ai_active_user():
    explainer = RecommendationExplainer()

    recommendation = {
        "title": "The Matrix (1999)",
        "genres": "Action|Sci-Fi",
        "final_score": 0.88,
        "content_score": 0.85,
        "collaborative_score": 0.90,
        "sentiment_score": 0.92,
        "content_available": True,
        "collaborative_available": True,
        "sentiment_available": True,
        "effective_weights": {"content": 0.45, "collaborative": 0.40, "sentiment": 0.15},
        "is_cold_start": False
    }

    user_ratings = [
        {"movieId": 79132, "rating": 5.0}, # Inception
        {"movieId": 109487, "rating": 4.5} # Interstellar
    ]

    similar_movies_watched = [
        {"movie_id": 79132, "title": "Inception (2010)", "similarity_score": 0.84, "user_rating": 5.0}
    ]

    sentiment_data = {
        "analyzed_reviews": 4,
        "positive_count": 4,
        "negative_count": 0,
        "positive_ratio": 1.0,
        "average_confidence": 0.96,
        "sample_quote": "A revolutionary triumph of visual effects."
    }

    explanation = explainer.explain_recommendation(
        movie_id=2571,
        recommendation=recommendation,
        user_ratings=user_ratings,
        preferred_genres=["Sci-Fi"],
        similar_movies_watched=similar_movies_watched,
        sentiment_data=sentiment_data
    )

    assert explanation["movie_id"] == 2571
    assert explanation["final_score"] == 0.88
    assert "Sci-Fi" in explanation["matching_genres"]
    assert len(explanation["similar_movies_watched"]) == 1
    assert explanation["similar_movies_watched"][0]["title"] == "Inception (2010)"

    # Verify natural language text contains key evidence
    narrative = explanation["natural_language_explanation"]
    assert "The Matrix (1999)" in narrative
    assert "Inception (2010)" in narrative
    assert "Content relevance contributed" in narrative
    assert "Collaborative filtering contributed" in narrative


def test_explainable_ai_cold_start_user():
    explainer = RecommendationExplainer()

    recommendation = {
        "title": "Toy Story (1995)",
        "genres": "Animation|Children|Comedy",
        "final_score": 0.75,
        "content_score": 0.75,
        "collaborative_score": None,
        "sentiment_score": None,
        "content_available": True,
        "collaborative_available": False,
        "sentiment_available": False,
        "effective_weights": {"content": 1.0},
        "is_cold_start": True
    }

    explanation = explainer.explain_recommendation(
        movie_id=1,
        recommendation=recommendation,
        user_ratings=[],
        preferred_genres=["Animation"],
        similar_movies_watched=[],
        sentiment_data=None
    )

    assert explanation["data_coverage"]["is_cold_start"] is True
    assert explanation["data_coverage"]["collaborative_available"] is False
    assert explanation["data_coverage"]["sentiment_available"] is False

    narrative = explanation["natural_language_explanation"]
    assert "insufficient personal rating history" in narrative
    assert "Animation" in narrative
