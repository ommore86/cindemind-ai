"""
CineMind AI — Movie Review Sentiment Classifier
Pretrained Transformer-based sentiment classifier with batching, truncation, and caching.
"""

import logging
import threading
from typing import List, Dict, Any, Union

logger = logging.getLogger("CineMind-SentimentClassifier")

DEFAULT_MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


class SentimentClassifier:
    """
    Singleton wrapper around Hugging Face sequence classification pipeline.
    Reuses model in memory and supports batch inference.
    Lazily loads the transformer pipeline only on demand to prevent memory bloat on startup.
    """
    _instance = None
    _pipeline = None
    _pipeline_loaded = False
    _load_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SentimentClassifier, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: str = "cpu"):
        self.model_name = model_name
        self.device = device

    def _ensure_pipeline(self):
        """Lazily initialize the Hugging Face pipeline only when inference is actually requested."""
        if self._pipeline_loaded:
            return self._pipeline

        with self._load_lock:
            if self._pipeline_loaded:
                return self._pipeline

            try:
                logger.info(f"Lazily loading sentiment analysis model: {self.model_name} on {self.device}...")
                import torch
                from transformers import pipeline

                device_id = 0 if self.device == "cuda" and torch.cuda.is_available() else -1
                self._pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    device=device_id,
                    truncation=True,
                    max_length=512
                )
                logger.info("Sentiment analysis model loaded successfully.")
            except Exception as e:
                logger.warning(
                    f"Could not load transformer model '{self.model_name}': {e}. "
                    "Using lexical rule-based sentiment fallback."
                )
                self._pipeline = None
            finally:
                self._pipeline_loaded = True

        return self._pipeline

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

        pipe = self._ensure_pipeline()
        if pipe:
            try:
                res = pipe(clean_text)[0]
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

        pipe = self._ensure_pipeline()
        if pipe and texts:
            try:
                hf_outputs = pipe(texts, batch_size=batch_size, truncation=True, max_length=512)
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
