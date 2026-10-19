"""
CineMind AI — Movie Review Sentiment Classifier
Pretrained Transformer-based sentiment classifier with batching, truncation, and caching.
"""

import logging
from typing import List, Dict, Any, Union
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger("CineMind-SentimentClassifier")

DEFAULT_MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


class SentimentClassifier:
    """
    Singleton wrapper around Hugging Face sequence classification pipeline.
    Reuses model in memory and supports batch inference.
    """
    _instance = None
    _pipeline = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SentimentClassifier, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: str = "cpu"):
        if self._pipeline is None:
            logger.info(f"Loading sentiment analysis model: {model_name} on {device}...")
            try:
                device_id = 0 if device == "cuda" and torch.cuda.is_available() else -1
                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model=model_name,
                    device=device_id,
                    truncation=True,
                    max_length=512
                )
                self.model_name = model_name
                logger.info("Sentiment analysis model loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load transformer model '{model_name}': {e}. Using rule-based fallback.")
                self._pipeline = None

    def predict_one(self, text: str) -> Dict[str, Any]:
        """Classify a single review text with validation for empty/long strings."""
        if not text or not str(text).strip():
            return {
                "label": "NEUTRAL",
                "score": 0.5,
                "confidence": 0.5,
                "is_empty": True
            }
            
        clean_text = str(text).strip()
        if len(clean_text) > 2000:
            clean_text = clean_text[:2000]

        if self._pipeline:
            try:
                res = self._pipeline(clean_text)[0]
                label = res["label"].upper() # POSITIVE or NEGATIVE
                confidence = float(res["score"])
                return {
                    "label": label,
                    "confidence": round(confidence, 4),
                    "is_empty": False
                }
            except Exception as e:
                logger.error(f"Inference error: {e}")
                
        # Rule-based fallback if model is unavailable
        return self._rule_based_fallback(clean_text)

    def predict_batch(self, reviews: List[Dict[str, Any]], batch_size: int = 16) -> List[Dict[str, Any]]:
        """
        Process batches of reviews while strictly preserving reviewId and movieId.
        Each review dict should contain: {'movieId': int, 'reviewId': str, 'reviewText': str}
        """
        results = []
        if not reviews:
            return results

        texts = []
        indices_to_predict = []

        for idx, rev in enumerate(reviews):
            raw_text = rev.get("reviewText", "")
            if not raw_text or not str(raw_text).strip():
                results.append({
                    **rev,
                    "predicted_sentiment": "NEUTRAL",
                    "sentiment_confidence": 0.5,
                    "is_empty": True
                })
            else:
                texts.append(str(raw_text).strip()[:2000])
                indices_to_predict.append(idx)
                results.append({**rev})

        if self._pipeline and texts:
            try:
                hf_outputs = self._pipeline(texts, batch_size=batch_size, truncation=True, max_length=512)
                for i, out in enumerate(hf_outputs):
                    orig_idx = indices_to_predict[i]
                    results[orig_idx]["predicted_sentiment"] = out["label"].upper()
                    results[orig_idx]["sentiment_confidence"] = round(float(out["score"]), 4)
                    results[orig_idx]["is_empty"] = False
            except Exception as e:
                logger.error(f"Batch inference failed: {e}. Falling back to single-item analysis.")
                for i, text in enumerate(texts):
                    orig_idx = indices_to_predict[i]
                    pred = self._rule_based_fallback(text)
                    results[orig_idx]["predicted_sentiment"] = pred["label"]
                    results[orig_idx]["sentiment_confidence"] = pred["confidence"]
                    results[orig_idx]["is_empty"] = False
        else:
            for i, text in enumerate(texts):
                orig_idx = indices_to_predict[i]
                pred = self._rule_based_fallback(text)
                results[orig_idx]["predicted_sentiment"] = pred["label"]
                results[orig_idx]["sentiment_confidence"] = pred["confidence"]
                results[orig_idx]["is_empty"] = False

        return results

    def _rule_based_fallback(self, text: str) -> Dict[str, Any]:
        """Lexical sentiment fallback when transformer inference is unavailable."""
        pos_words = {"great", "masterpiece", "brilliant", "triumph", "exceptional", "loved", "superb",
                     "best", "perfect", "good", "wonderful", "amazing", "exciting", "heartfelt", "stellar"}
        neg_words = {"bad", "terrible", "awful", "boring", "worst", "waste", "poor", "disappointing",
                     "clunky", "dated", "formulaic", "predictable", "nihilism", "contrived", "ruined"}
        
        lower = text.lower().split()
        pos_count = sum(1 for w in lower if w in pos_words)
        neg_count = sum(1 for w in lower if w in neg_words)

        if pos_count > neg_count:
            return {"label": "POSITIVE", "confidence": 0.85, "is_empty": False}
        elif neg_count > pos_count:
            return {"label": "NEGATIVE", "confidence": 0.85, "is_empty": False}
        else:
            return {"label": "POSITIVE", "confidence": 0.60, "is_empty": False}


# Singleton accessor
_classifier_instance = None

def get_sentiment_classifier() -> SentimentClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SentimentClassifier()
    return _classifier_instance
