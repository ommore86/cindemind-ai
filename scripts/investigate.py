import os
import sys
import pandas as pd
import numpy as np

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender
from app.ml.recommendation.hybrid_engine import HybridRecommendationEngine
from app.ml.recommendation.evaluation import (
    compute_precision_recall_at_k,
    compute_ndcg_at_k,
    split_train_test_ratings
)

movies_path = "data/processed/movies_processed.csv"
ratings_path = "data/processed/ratings_cleaned.csv"

movies_df = pd.read_csv(movies_path)
ratings_df = pd.read_csv(ratings_path)

train_ratings, test_ratings = split_train_test_ratings(ratings_df, test_ratio=0.20, random_state=42)

content_rec = ContentBasedRecommender(max_features=5000)
content_rec.fit(movies_df)

collab_rec = CollaborativeRecommender(n_factors=20)
collab_rec.fit(train_ratings)

hybrid_rec = HybridRecommendationEngine(
    content_recommender=content_rec,
    collaborative_recommender=collab_rec,
    w_content=0.45,
    w_collab=0.40,
    w_sentiment=0.15
)

# Test users
test_users = []
user_test_relevant = {}
for uid, group in test_ratings.groupby("userId"):
    rel = set(group[group["rating"] >= 3.5]["movieId"].tolist())
    if len(rel) >= 2:
        test_users.append(uid)
        user_test_relevant[uid] = rel

print(f"Total eligible test users: {len(test_users)}")

train_user_ratings_map = {
    uid: group.to_dict(orient="records")
    for uid, group in train_ratings.groupby("userId")
}

for uid in test_users[:5]:
    ground_truth = user_test_relevant[uid]
    u_train = train_user_ratings_map.get(uid, [])
    rated_mids = {r["movieId"] for r in u_train}
    
    cb_res = content_rec.recommend_for_user(u_train, top_n=10, exclude_rated=True)
    cb_mids = [item["movie_id"] for item in cb_res]
    
    cf_res = collab_rec.recommend_for_user(uid, rated_movie_ids=rated_mids, top_n=10)
    cf_mids = [item["movie_id"] for item in cf_res]
    
    hyb_res = hybrid_rec.recommend(user_id=uid, user_ratings=u_train, top_n=10, exclude_rated=True)
    hyb_mids = [item["movie_id"] for item in hyb_res]
    
    p_cb, r_cb = compute_precision_recall_at_k(cb_mids, ground_truth, k=10)
    p_cf, r_cf = compute_precision_recall_at_k(cf_mids, ground_truth, k=10)
    p_hyb, r_hyb = compute_precision_recall_at_k(hyb_mids, ground_truth, k=10)
    
    print(f"\nUser {uid}: Ground truth size: {len(ground_truth)}")
    print(f"  CF hits: {set(cf_mids) & ground_truth} -> P@10={p_cf:.2f}, R@10={r_cf:.2f}")
    print(f"  CB hits: {set(cb_mids) & ground_truth} -> P@10={p_cb:.2f}, R@10={r_cb:.2f}")
    print(f"  Hyb hits: {set(hyb_mids) & ground_truth} -> P@10={p_hyb:.2f}, R@10={r_hyb:.2f}")
    
    # Inspect top 5 scores for CF vs Hybrid
    print("  CF top 3 recommendations:")
    for item in cf_res[:3]:
        print(f"    mid={item['movie_id']}, score={item['collaborative_score']}, pred_r={item['predicted_rating']}")
    print("  Hybrid top 3 recommendations:")
    for item in hyb_res[:3]:
        print(f"    mid={item['movie_id']}, final={item['final_score']}, cont={item['content_score']}, collab={item['collaborative_score']}, sent={item['sentiment_score']}")
