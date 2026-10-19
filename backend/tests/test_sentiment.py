"""
Unit Tests for Sentiment Classifier & Aggregator
"""

import pytest
from app.ml.sentiment.classifier import get_sentiment_classifier, SentimentClassifier
from app.ml.sentiment.aggregator import SentimentAggregator


def test_sentiment_classifier_empty_and_long_text():
    classifier = get_sentiment_classifier()

    # Empty text
    res_empty = classifier.predict_one("")
    assert res_empty["is_empty"] is True

    # None text
    res_none = classifier.predict_one(None)
    assert res_none["is_empty"] is True

    # Very long text (exceeding 2000 chars)
    long_text = "Masterpiece! " * 300
    res_long = classifier.predict_one(long_text)
    assert res_long["is_empty"] is False
    assert res_long["label"] in ["POSITIVE", "NEGATIVE"]


def test_sentiment_batch_inference_preserves_metadata():
    classifier = get_sentiment_classifier()

    batch = [
        {"movieId": 1, "reviewId": "rev_001", "reviewText": "An extraordinary cinematic masterpiece with superb acting."},
        {"movieId": 1, "reviewId": "rev_002", "reviewText": "Dreadful, boring, and predictable garbage."},
        {"movieId": 2, "reviewId": "rev_003", "reviewText": ""} # empty review
    ]

    results = classifier.predict_batch(batch)

    assert len(results) == 3
    # Check that movieId and reviewId are preserved exactly
    assert results[0]["movieId"] == 1
    assert results[0]["reviewId"] == "rev_001"
    assert results[0]["predicted_sentiment"] == "POSITIVE"

    assert results[1]["movieId"] == 1
    assert results[1]["reviewId"] == "rev_002"
    assert results[1]["predicted_sentiment"] == "NEGATIVE"

    assert results[2]["is_empty"] is True


def test_sentiment_aggregator_honesty():
    mock_predictions = [
        {"movieId": 1, "predicted_sentiment": "POSITIVE", "sentiment_confidence": 0.95, "is_empty": False},
        {"movieId": 1, "predicted_sentiment": "POSITIVE", "sentiment_confidence": 0.85, "is_empty": False},
        {"movieId": 1, "predicted_sentiment": "NEGATIVE", "sentiment_confidence": 0.90, "is_empty": False},
    ]

    # Movie 1 aggregation
    agg_1 = SentimentAggregator.aggregate_for_movie(1, mock_predictions)
    assert agg_1 is not None
    assert agg_1["movie_id"] == 1
    assert agg_1["analyzed_reviews"] == 3
    assert agg_1["positive_count"] == 2
    assert agg_1["negative_count"] == 1
    assert round(agg_1["positive_ratio"], 2) == 0.67
    assert 0.0 <= agg_1["aggregate_sentiment_score"] <= 1.0

    # Movie with NO reviews: MUST return None (explicit unavailable sentiment)
    agg_unreviewed = SentimentAggregator.aggregate_for_movie(999, mock_predictions)
    assert agg_unreviewed is None
