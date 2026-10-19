import os
import sys
import pandas as pd
import numpy as np

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.recommendation.content_based import ContentBasedRecommender
from app.ml.recommendation.collaborative import CollaborativeRecommender
from app.ml.recommendation.evaluation import (
    compute_precision_recall_at_k,
    compute_ndcg_at_k,
    split_train_test_ratings
)

movies_df = pd.read_csv("data/processed/movies_processed.csv")
ratings_df = pd.read_csv("data/processed/ratings_cleaned.csv")

train_ratings, test_ratings = split_train_test_ratings(ratings_df, test_ratio=0.20, random_state=42)

cb = ContentBasedRecommender(max_features=5000)
cb.fit(movies_df)

cf = CollaborativeRecommender(n_factors=20)
cf.fit(train_ratings)

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

# Baseline CF
p_cf, r_cf, ndcg_cf = [], [], []
for uid in evaluated_users:
    gt = user_test_relevant[uid]
    u_train = train_user_ratings_map.get(uid, [])
    rated_mids = {r["movieId"] for r in u_train}
    cf_res = cf.recommend_for_user(uid, rated_movie_ids=rated_mids, top_n=10)
    cf_mids = [item["movie_id"] for item in cf_res]
    p, r = compute_precision_recall_at_k(cf_mids, gt, k=10)
    n = compute_ndcg_at_k(cf_mids, gt, k=10)
    p_cf.append(p); r_cf.append(r); ndcg_cf.append(n)

print(f"CF Baseline: P@10={np.mean(p_cf):.4f}, R@10={np.mean(r_cf):.4f}, NDCG@10={np.mean(ndcg_cf):.4f}")

# Baseline CB
p_cb, r_cb, ndcg_cb = [], [], []
for uid in evaluated_users:
    gt = user_test_relevant[uid]
    u_train = train_user_ratings_map.get(uid, [])
    cb_res = cb.recommend_for_user(u_train, top_n=10, exclude_rated=True)
    cb_mids = [item["movie_id"] for item in cb_res]
    p, r = compute_precision_recall_at_k(cb_mids, gt, k=10)
    n = compute_ndcg_at_k(cb_mids, gt, k=10)
    p_cb.append(p); r_cb.append(r); ndcg_cb.append(n)

print(f"CB Baseline: P@10={np.mean(p_cb):.4f}, R@10={np.mean(r_cb):.4f}, NDCG@10={np.mean(ndcg_cb):.4f}")

# Test Hybrid Strategy 1: Min-Max normalized CF + Content
for w_c, w_cf in [(0.45, 0.40), (0.30, 0.70), (0.20, 0.80), (0.15, 0.85)]:
    p_hyb, r_hyb, ndcg_hyb = [], [], []
    for uid in evaluated_users:
        gt = user_test_relevant[uid]
        u_train = train_user_ratings_map.get(uid, [])
        rated_mids = {r["movieId"] for r in u_train}
        candidates = movies_df[~movies_df["movieId"].isin(rated_mids)]
        
        c_res = cb.recommend_for_user(u_train, top_n=len(candidates), exclude_rated=True)
        c_map = {x["movie_id"]: x["content_score"] for x in c_res}
        
        u_idx = cf.user_to_idx[uid]
        u_vec = cf.user_factors[u_idx]
        cf_preds = np.dot(u_vec, cf.item_factors.T) + cf.user_means[u_idx]
        
        # Min-max scaling
        valid_mids = [mid for mid in candidates["movieId"] if mid in cf.movie_to_idx]
        preds_list = [cf_preds[cf.movie_to_idx[mid]] for mid in valid_mids]
        min_p = min(preds_list)
        max_p = max(preds_list)
        rng = max_p - min_p if max_p > min_p else 1.0
        
        hyb_scores = []
        for mid in candidates["movieId"]:
            cs = c_map.get(mid, 0.0)
            if mid in cf.movie_to_idx:
                raw_pred = cf_preds[cf.movie_to_idx[mid]]
                cfs = (raw_pred - min_p) / rng
                # Weights renormalized
                total_w = w_c + w_cf
                final = (w_c / total_w) * cs + (w_cf / total_w) * cfs
            else:
                # Missing CF for this movie
                final = cs * (w_c / (w_c + w_cf)) # penalize lack of CF
            hyb_scores.append((mid, final))
            
        hyb_scores.sort(key=lambda x: x[1], reverse=True)
        top_mids = [x[0] for x in hyb_scores[:10]]
        p, r = compute_precision_recall_at_k(top_mids, gt, k=10)
        n = compute_ndcg_at_k(top_mids, gt, k=10)
        p_hyb.append(p); r_hyb.append(r); ndcg_hyb.append(n)
        
    print(f"Hybrid (w_c={w_c}, w_cf={w_cf}): P@10={np.mean(p_hyb):.4f}, R@10={np.mean(r_hyb):.4f}, NDCG@10={np.mean(ndcg_hyb):.4f}")
