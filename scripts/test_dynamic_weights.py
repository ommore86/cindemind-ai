import os
import sys
import pandas as pd
import numpy as np

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender
from app.ml.sentiment.classifier import get_sentiment_classifier
from app.ml.sentiment.aggregator import SentimentAggregator
from app.ml.recommendation.evaluation import (
    compute_precision_recall_at_k,
    compute_ndcg_at_k,
    split_train_test_ratings
)

movies_df = pd.read_csv("data/processed/movies_processed.csv")
ratings_df = pd.read_csv("data/processed/ratings_cleaned.csv")
reviews_path = "data/processed/reviews_cleaned.csv"

train_ratings, test_ratings = split_train_test_ratings(ratings_df, test_ratio=0.20, random_state=42)

cb = ContentBasedRecommender(max_features=5000)
cb.fit(movies_df)

cf = CollaborativeRecommender(n_factors=20)
cf.fit(train_ratings)

sentiment_aggregates = {}
if os.path.exists(reviews_path):
    reviews_df = pd.read_csv(reviews_path)
    classifier = get_sentiment_classifier()
    preds = classifier.predict_batch(reviews_df.to_dict(orient="records"))
    sentiment_aggregates = SentimentAggregator.aggregate_all_movies(preds)

test_users = []
user_test_relevant = {}
for uid, group in test_ratings.groupby("userId"):
    rel = set(group[group["rating"] >= 3.5]["movieId"].tolist())
    if len(rel) >= 2:
        test_users.append(uid)
        user_test_relevant[uid] = rel

train_user_ratings_map = {
    uid: group.to_dict(orient="records")
    for uid, group in train_ratings.groupby("userId")
}

evaluated_users = test_users[:50]

# Test: What if Hybrid uses min-max normalized CF with dynamic weights preserved?
w_content = 0.45
w_collab = 0.40
w_sentiment = 0.15

p_hyb, r_hyb, ndcg_hyb = [], [], []

for uid in evaluated_users:
    gt = user_test_relevant[uid]
    u_train = train_user_ratings_map.get(uid, [])
    rated_mids = {r["movieId"] for r in u_train}
    candidates = movies_df[~movies_df["movieId"].isin(rated_mids)]
    
    # 1. Content scores
    c_res = cb.recommend_for_user(u_train, top_n=len(candidates), exclude_rated=True)
    c_map = {x["movie_id"]: x["content_score"] for x in c_res}
    
    # 2. Collaborative scores with min-max normalization across candidate pool
    u_idx = cf.user_to_idx.get(uid)
    is_known_user = u_idx is not None
    
    cf_norm_map = {}
    if is_known_user:
        user_vec = cf.user_factors[u_idx]
        cf_preds = np.dot(user_vec, cf.item_factors.T) + cf.user_means[u_idx]
        
        valid_candidate_mids = [mid for mid in candidates["movieId"] if mid in cf.movie_to_idx]
        if valid_candidate_mids:
            cand_preds = [cf_preds[cf.movie_to_idx[mid]] for mid in valid_candidate_mids]
            min_p = min(cand_preds)
            max_p = max(cand_preds)
            rng = max_p - min_p if max_p > min_p else 1.0
            for mid in valid_candidate_mids:
                raw_pred = cf_preds[cf.movie_to_idx[mid]]
                cf_norm_map[mid] = float(np.clip((raw_pred - min_p) / rng, 0.0, 1.0))
                
    # 3. Dynamic weight combination
    scored_items = []
    for _, row in candidates.iterrows():
        mid = int(row["movieId"])
        c_score = c_map.get(mid, 0.0)
        c_available = True
        
        collab_score = cf_norm_map.get(mid)
        collab_available = collab_score is not None
        
        sentiment_score = None
        sentiment_available = False
        sentiment_meta = sentiment_aggregates.get(mid)
        if sentiment_meta and sentiment_meta.get("sentiment_available"):
            sentiment_score = sentiment_meta.get("aggregate_sentiment_score")
            sentiment_available = True
            
        active_weights = {}
        if c_available:
            active_weights["content"] = w_content
        if collab_available:
            active_weights["collaborative"] = w_collab
        if sentiment_available:
            active_weights["sentiment"] = w_sentiment
            
        total_active_w = sum(active_weights.values())
        if total_active_w > 0:
            normalized_weights = {k: v / total_active_w for k, v in active_weights.items()}
        else:
            normalized_weights = {"content": 1.0}
            
        final_score = 0.0
        if "content" in normalized_weights:
            final_score += normalized_weights["content"] * c_score
        if "collaborative" in normalized_weights and collab_score is not None:
            final_score += normalized_weights["collaborative"] * collab_score
        if "sentiment" in normalized_weights and sentiment_score is not None:
            final_score += normalized_weights["sentiment"] * sentiment_score
            
        scored_items.append((mid, final_score))
        
    scored_items.sort(key=lambda x: x[1], reverse=True)
    top_mids = [x[0] for x in scored_items[:10]]
    p, r = compute_precision_recall_at_k(top_mids, gt, k=10)
    n = compute_ndcg_at_k(top_mids, gt, k=10)
    p_hyb.append(p); r_hyb.append(r); ndcg_hyb.append(n)

print(f"Hybrid with Min-Max CF & Dynamic Weights: P@10={np.mean(p_hyb):.4f}, R@10={np.mean(r_hyb):.4f}, NDCG@10={np.mean(ndcg_hyb):.4f}")
