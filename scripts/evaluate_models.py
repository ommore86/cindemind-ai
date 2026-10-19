"""
CineMind AI — Model Evaluation and Comparison Script
Evaluates Content-Based, Collaborative, and Hybrid recommenders on a held-out test split.
Outputs reproducible Precision@K, Recall@K, NDCG@K, RMSE, and MAE to evaluation_report.json.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import pandas as pd
import numpy as np

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender
from app.ml.recommendation.hybrid_engine import HybridRecommendationEngine
from app.ml.sentiment.classifier import get_sentiment_classifier
from app.ml.sentiment.aggregator import SentimentAggregator
from app.ml.recommendation.evaluation import (
    compute_precision_recall_at_k,
    compute_ndcg_at_k,
    compute_rating_prediction_metrics,
    split_train_test_ratings
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CineMind-ModelEvaluator")


def main():
    parser = argparse.ArgumentParser(description="Evaluate CineMind AI Recommendation Models")
    parser.add_argument("--processed-dir", default="data/processed", help="Directory of processed data")
    parser.add_argument("--k", type=int, default=10, help="Cutoff K for ranking evaluation")
    parser.add_argument("--max-users", type=int, default=100, help="Number of test users to evaluate")
    args = parser.parse_args()

    movies_path = os.path.join(args.processed_dir, "movies_processed.csv")
    ratings_path = os.path.join(args.processed_dir, "ratings_cleaned.csv")
    reviews_path = os.path.join(args.processed_dir, "reviews_cleaned.csv")
    output_path = os.path.join(args.processed_dir, "evaluation_report.json")

    logger.info("Loading processed data for evaluation...")
    movies_df = pd.read_csv(movies_path)
    ratings_df = pd.read_csv(ratings_path)

    # 1. Train / Test Split
    train_ratings, test_ratings = split_train_test_ratings(ratings_df, test_ratio=0.20, random_state=42)

    # 2. Fit Models
    logger.info("Fitting Content-Based Recommender...")
    content_rec = ContentBasedRecommender(max_features=5000)
    content_rec.fit(movies_df)

    logger.info("Fitting Collaborative Recommender...")
    collab_rec = CollaborativeRecommender(n_factors=20)
    collab_rec.fit(train_ratings)

    # 3. Analyze reviews if available
    sentiment_aggregates = {}
    if os.path.exists(reviews_path):
        reviews_df = pd.read_csv(reviews_path)
        logger.info(f"Classifying {len(reviews_df)} authentic reviews...")
        classifier = get_sentiment_classifier()
        rev_records = reviews_df.to_dict(orient="records")
        preds = classifier.predict_batch(rev_records)
        sentiment_aggregates = SentimentAggregator.aggregate_all_movies(preds)

    logger.info("Initializing Hybrid Engine...")
    hybrid_rec = HybridRecommendationEngine(
        content_recommender=content_rec,
        collaborative_recommender=collab_rec,
        w_content=0.45,
        w_collab=0.40,
        w_sentiment=0.15
    )
    hybrid_rec.set_sentiment_aggregates(sentiment_aggregates)

    # 4. Collaborative Rating Prediction Metrics (RMSE / MAE)
    logger.info("Calculating Collaborative Rating Prediction Metrics (RMSE & MAE)...")
    pred_pairs = []
    for _, row in test_ratings.iterrows():
        u = int(row["userId"])
        m = int(row["movieId"])
        actual = float(row["rating"])
        pred, available = collab_rec.predict_rating(u, m)
        if available and pred is not None:
            pred_pairs.append((actual, pred))

    collab_rmse, collab_mae = compute_rating_prediction_metrics(pred_pairs)
    logger.info(f"Collaborative Filtering on {len(pred_pairs)} test ratings: RMSE={collab_rmse}, MAE={collab_mae}")

    # 5. Ranking Evaluation (Precision@K, Recall@K, NDCG@K)
    logger.info(f"Evaluating top-{args.k} ranking across models...")
    
    # Identify test users with at least 3 relevant items (rating >= 3.5)
    test_users = []
    user_test_relevant = {}
    for uid, group in test_ratings.groupby("userId"):
        rel = set(group[group["rating"] >= 3.5]["movieId"].tolist())
        if len(rel) >= 2:
            test_users.append(uid)
            user_test_relevant[uid] = rel

    evaluated_users = test_users[:args.max_users]
    logger.info(f"Evaluating on {len(evaluated_users)} eligible validation users...")

    metrics = {
        "content_based": {"precision": [], "recall": [], "ndcg": []},
        "collaborative": {"precision": [], "recall": [], "ndcg": []},
        "hybrid": {"precision": [], "recall": [], "ndcg": []}
    }

    train_user_ratings_map = {
        uid: group.to_dict(orient="records")
        for uid, group in train_ratings.groupby("userId")
    }

    all_catalog_mids = list(movies_df["movieId"].unique())

    for uid in evaluated_users:
        ground_truth = user_test_relevant[uid]
        u_train = train_user_ratings_map.get(uid, [])
        rated_mids = {r["movieId"] for r in u_train}
        candidate_mids = [mid for mid in all_catalog_mids if mid not in rated_mids]

        # Content-Based Ranking
        cb_res = content_rec.recommend_for_user(u_train, top_n=args.k, exclude_rated=True)
        cb_mids = [item["movie_id"] for item in cb_res]
        p_cb, r_cb = compute_precision_recall_at_k(cb_mids, ground_truth, k=args.k)
        ndcg_cb = compute_ndcg_at_k(cb_mids, ground_truth, k=args.k)
        metrics["content_based"]["precision"].append(p_cb)
        metrics["content_based"]["recall"].append(r_cb)
        metrics["content_based"]["ndcg"].append(ndcg_cb)

        # Collaborative Ranking (evaluated on exact same candidates)
        cf_res = collab_rec.recommend_for_user(uid, rated_movie_ids=rated_mids, candidate_movie_ids=candidate_mids, top_n=args.k)
        cf_mids = [item["movie_id"] for item in cf_res]
        p_cf, r_cf = compute_precision_recall_at_k(cf_mids, ground_truth, k=args.k)
        ndcg_cf = compute_ndcg_at_k(cf_mids, ground_truth, k=args.k)
        metrics["collaborative"]["precision"].append(p_cf)
        metrics["collaborative"]["recall"].append(r_cf)
        metrics["collaborative"]["ndcg"].append(ndcg_cf)

        # Hybrid Ranking
        hyb_res = hybrid_rec.recommend(
            user_id=uid,
            user_ratings=u_train,
            top_n=args.k,
            exclude_rated=True
        )
        hyb_mids = [item["movie_id"] for item in hyb_res]
        p_hyb, r_hyb = compute_precision_recall_at_k(hyb_mids, ground_truth, k=args.k)
        ndcg_hyb = compute_ndcg_at_k(hyb_mids, ground_truth, k=args.k)
        metrics["hybrid"]["precision"].append(p_hyb)
        metrics["hybrid"]["recall"].append(r_hyb)
        metrics["hybrid"]["ndcg"].append(ndcg_hyb)

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "k_value": args.k,
        "sample_size_users": len(evaluated_users),
        "test_ratings_evaluated": len(pred_pairs),
        "models": {
            "content_based": {
                "name": "Content-Based Filtering (TF-IDF + Cosine)",
                "precision_at_k": round(float(np.mean(metrics["content_based"]["precision"])), 4),
                "recall_at_k": round(float(np.mean(metrics["content_based"]["recall"])), 4),
                "ndcg_at_k": round(float(np.mean(metrics["content_based"]["ndcg"])), 4),
                "rmse": None,
                "mae": None
            },
            "collaborative": {
                "name": "Collaborative Filtering (Truncated SVD Matrix Factorization)",
                "precision_at_k": round(float(np.mean(metrics["collaborative"]["precision"])), 4),
                "recall_at_k": round(float(np.mean(metrics["collaborative"]["recall"])), 4),
                "ndcg_at_k": round(float(np.mean(metrics["collaborative"]["ndcg"])), 4),
                "rmse": collab_rmse,
                "mae": collab_mae
            },
            "hybrid": {
                "name": "Hybrid Engine (Content + Collaborative + Sentiment)",
                "precision_at_k": round(float(np.mean(metrics["hybrid"]["precision"])), 4),
                "recall_at_k": round(float(np.mean(metrics["hybrid"]["recall"])), 4),
                "ndcg_at_k": round(float(np.mean(metrics["hybrid"]["ndcg"])), 4),
                "rmse": None,
                "mae": None
            }
        },
        "notes": [
            "Evaluated using a 80/20 stratified user rating train/test split.",
            "Relevant items defined as test ratings with rating >= 3.5.",
            "RMSE and MAE are only applicable to Collaborative Filtering which directly predicts explicit star ratings.",
            "Hybrid recommender balances personalization, catalog discovery, and positive sentiment evidence."
        ]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Evaluation report successfully saved to {output_path}")
    logger.info(json.dumps(report["models"], indent=2))


if __name__ == "__main__":
    main()
