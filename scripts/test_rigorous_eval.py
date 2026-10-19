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

all_catalog_mids = list(movies_df["movieId"].unique())

p_cb, r_cb, n_cb = [], [], []
p_cf, r_cf, n_cf = [], [], []
p_hyb, r_hyb, n_hyb = [], [], []

w_c, w_cf, w_s = 0.45, 0.40, 0.15

for uid in evaluated_users:
    gt = user_test_relevant[uid]
    u_train = train_user_ratings_map.get(uid, [])
    rated_mids = {r["movieId"] for r in u_train}
    candidate_mids = [mid for mid in all_catalog_mids if mid not in rated_mids]
    candidate_set = set(candidate_mids)
    candidates_df = movies_df[movies_df["movieId"].isin(candidate_set)]

    # 1. Content-based
    cb_res = cb.recommend_for_user(u_train, top_n=10, exclude_rated=True)
    cb_mids = [x["movie_id"] for x in cb_res]
    p, r = compute_precision_recall_at_k(cb_mids, gt, k=10)
    n = compute_ndcg_at_k(cb_mids, gt, k=10)
    p_cb.append(p); r_cb.append(r); n_cb.append(n)

    # 2. Collaborative (evaluated on exact same candidates)
    cf_res = cf.recommend_for_user(uid, rated_movie_ids=rated_mids, candidate_movie_ids=candidate_mids, top_n=10)
    cf_mids = [x["movie_id"] for x in cf_res]
    p, r = compute_precision_recall_at_k(cf_mids, gt, k=10)
    n = compute_ndcg_at_k(cf_mids, gt, k=10)
    p_cf.append(p); r_cf.append(r); n_cf.append(n)

    # 3. Hybrid with vectorized user-level min-max normalization
    c_res = cb.recommend_for_user(u_train, top_n=len(candidates_df), exclude_rated=True)
    c_map = {x["movie_id"]: x["content_score"] for x in c_res}

    u_idx = cf.user_to_idx.get(uid)
    cf_norm_map = {}
    if u_idx is not None:
        user_vec = cf.user_factors[u_idx]
        dots = np.dot(user_vec, cf.item_factors.T)
        d_min, d_max = dots.min(), dots.max()
        d_rng = d_max - d_min if d_max > d_min else 1.0
        norm_dots = (dots - d_min) / d_rng
        for mid, idx in cf.movie_to_idx.items():
            if mid in candidate_set:
                cf_norm_map[mid] = float(norm_dots[idx])

    scored = []
    for mid in candidate_mids:
        c_score = c_map.get(mid, 0.0)
        c_avail = True

        collab_score = cf_norm_map.get(mid)
        collab_avail = collab_score is not None

        sent_meta = sentiment_aggregates.get(mid)
        sent_avail = sent_meta is not None and sent_meta.get("sentiment_available", False)
        sent_score = sent_meta.get("aggregate_sentiment_score") if sent_avail else None

        # Dynamic weight redistribution
        act_w = {}
        if c_avail:
            act_w["content"] = w_c
        if collab_avail:
            act_w["collaborative"] = w_cf
        if sent_avail:
            act_w["sentiment"] = w_s

        tot_w = sum(act_w.values())
        norm_w = {k: v / tot_w for k, v in act_w.items()}

        final = 0.0
        if "content" in norm_w:
            final += norm_w["content"] * c_score
        if "collaborative" in norm_w and collab_score is not None:
            final += norm_w["collaborative"] * collab_score
        if "sentiment" in norm_w and sent_score is not None:
            final += norm_w["sentiment"] * sent_score

        scored.append((mid, final))

    scored.sort(key=lambda x: x[1], reverse=True)
    hyb_mids = [x[0] for x in scored[:10]]
    p, r = compute_precision_recall_at_k(hyb_mids, gt, k=10)
    n = compute_ndcg_at_k(hyb_mids, gt, k=10)
    p_hyb.append(p); r_hyb.append(r); n_hyb.append(n)

print(f"Content-Based:  P@10={np.mean(p_cb):.4f}, R@10={np.mean(r_cb):.4f}, NDCG@10={np.mean(n_cb):.4f}")
print(f"Collaborative:  P@10={np.mean(p_cf):.4f}, R@10={np.mean(r_cf):.4f}, NDCG@10={np.mean(n_cf):.4f}")
print(f"Hybrid:         P@10={np.mean(p_hyb):.4f}, R@10={np.mean(r_hyb):.4f}, NDCG@10={np.mean(n_hyb):.4f}")
