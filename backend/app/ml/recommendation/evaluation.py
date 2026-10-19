"""
CineMind AI — Recommendation System Evaluation Metrics
Implements Precision@K, Recall@K, NDCG@K, RMSE, and MAE with train/test splits.
"""

import logging
import math
from typing import List, Dict, Any, Tuple, Set
import numpy as np
import pandas as pd

logger = logging.getLogger("CineMind-Evaluation")


def compute_precision_recall_at_k(
    recommended_items: List[int],
    ground_truth_relevant: Set[int],
    k: int = 10
) -> Tuple[float, float]:
    """
    Compute Precision@K and Recall@K.
    An item is relevant if it exists in the user's test set with high rating (e.g. >= 3.5).
    """
    if not ground_truth_relevant or k <= 0:
        return 0.0, 0.0

    top_k = recommended_items[:k]
    hits = sum(1 for item in top_k if item in ground_truth_relevant)
    
    precision = hits / float(k)
    recall = hits / float(len(ground_truth_relevant))
    return precision, recall


def compute_ndcg_at_k(
    recommended_items: List[int],
    ground_truth_relevant: Set[int],
    k: int = 10
) -> float:
    """
    Compute Normalized Discounted Cumulative Gain (NDCG@K).
    Binary relevance: 1 if item in relevant set, 0 otherwise.
    """
    if not ground_truth_relevant or k <= 0:
        return 0.0

    top_k = recommended_items[:k]
    dcg = 0.0
    for i, item in enumerate(top_k):
        if item in ground_truth_relevant:
            dcg += 1.0 / math.log2((i + 1) + 1) # log2(rank + 1)

    # Ideal DCG: all hits at top ranks
    ideal_hits = min(k, len(ground_truth_relevant))
    idcg = sum(1.0 / math.log2((i + 1) + 1) for i in range(ideal_hits))

    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def compute_rating_prediction_metrics(
    predictions: List[Tuple[float, float]] # (actual, predicted)
) -> Tuple[float, float]:
    """
    Compute RMSE and MAE for rating prediction models.
    """
    if not predictions:
        return 0.0, 0.0

    actuals = np.array([p[0] for p in predictions])
    preds = np.array([p[1] for p in predictions])

    errors = preds - actuals
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    mae = float(np.mean(np.abs(errors)))
    return round(rmse, 4), round(mae, 4)


def split_train_test_ratings(
    ratings_df: pd.DataFrame,
    test_ratio: float = 0.20,
    min_user_ratings: int = 5,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Temporal or stratified split of ratings per user to avoid data leakage.
    Ensures held-out test ratings are only used for evaluation.
    """
    np.random.seed(random_state)
    
    train_rows = []
    test_rows = []

    for user_id, group in ratings_df.groupby("userId"):
        if len(group) < min_user_ratings:
            train_rows.append(group)
            continue

        shuffled = group.sample(frac=1.0, random_state=random_state)
        n_test = max(1, int(len(shuffled) * test_ratio))
        
        test_rows.append(shuffled.iloc[:n_test])
        train_rows.append(shuffled.iloc[n_test:])

    train_df = pd.concat(train_rows, ignore_index=True)
    test_df = pd.concat(test_rows, ignore_index=True)
    
    logger.info(f"Split dataset: {len(train_df)} train ratings, {len(test_df)} test ratings.")
    return train_df, test_df
