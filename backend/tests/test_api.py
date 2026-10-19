"""
Integration Tests for FastAPI REST Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "CineMind AI"


def test_get_movies_pagination():
    response = client.get("/api/v1/movies?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) <= 5
    if data["items"]:
        first = data["items"][0]
        assert "movie_id" in first
        assert "title" in first
        assert "genres" in first


def test_get_movie_detail():
    # Retrieve movie 1 (Toy Story)
    response = client.get("/api/v1/movies/1")
    assert response.status_code == 200
    data = response.json()
    assert data["movie_id"] == 1
    assert "Toy Story" in data["title"]
    assert "genres" in data


def test_get_unknown_movie_returns_404():
    response = client.get("/api/v1/movies/999999")
    assert response.status_code == 404


def test_get_user_recommendations():
    response = client.get("/api/v1/recommendations/1?top_n=5")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert "items" in data
    assert len(data["items"]) > 0
    first = data["items"][0]
    assert "final_score" in first
    assert "effective_weights" in first


def test_get_recommendation_explanation():
    response = client.get("/api/v1/recommendations/1/1/explanation")
    assert response.status_code == 200
    data = response.json()
    assert data["movie_id"] == 1
    assert "natural_language_explanation" in data
    assert "scores" in data
    assert "effective_weights" in data


def test_analytics_endpoints():
    # Overview
    res_ov = client.get("/api/v1/analytics/overview")
    assert res_ov.status_code == 200
    assert "total_movies" in res_ov.json()

    # Ratings
    res_rat = client.get("/api/v1/analytics/ratings")
    assert res_rat.status_code == 200
    assert isinstance(res_rat.json(), list)

    # Genres
    res_gen = client.get("/api/v1/analytics/genres")
    assert res_gen.status_code == 200
    assert isinstance(res_gen.json(), list)

    # Sentiment
    res_sent = client.get("/api/v1/analytics/sentiment")
    assert res_sent.status_code == 200
    assert "positive_reviews" in res_sent.json()

    # Recommendations Benchmarks
    res_bm = client.get("/api/v1/analytics/recommendations")
    assert res_bm.status_code == 200
    assert "benchmarks" in res_bm.json()


def test_realtime_sentiment_inference_api():
    payload = {"text": "A stunning visual masterclass with profound emotional resonance."}
    response = client.post("/api/v1/sentiment/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "POSITIVE"
    assert data["confidence"] > 0.5
