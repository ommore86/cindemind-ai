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
from app.ml.sentiment.classifier import get_sentiment_classifier
from app.ml.sentiment.aggregator import SentimentAggregator
from app.ml.recommendation.evaluation import split_train_test_ratings

movies_df = pd.read_csv("data/processed/movies_processed.csv")
ratings_df = pd.read_csv("data/processed/ratings_cleaned.csv")
reviews_path = "data/processed/reviews_cleaned.csv"

train_ratings, test_ratings = split_train_test_ratings(ratings_df, test_ratio=0.20, random_state=42)

content_rec = ContentBasedRecommender(max_features=5000)
content_rec.fit(movies_df)

collab_rec = CollaborativeRecommender(n_factors=20)
collab_rec.fit(train_ratings)

sentiment_aggregates = {}
if os.path.exists(reviews_path):
    reviews_df = pd.read_csv(reviews_path)
    classifier = get_sentiment_classifier()
    preds = classifier.predict_batch(reviews_df.to_dict(orient="records"))
    sentiment_aggregates = SentimentAggregator.aggregate_all_movies(preds)

hybrid_rec = HybridRecommendationEngine(
    content_recommender=content_rec,
    collaborative_recommender=collab_rec,
    w_content=0.45,
    w_collab=0.40,
    w_sentiment=0.15
)
hybrid_rec.set_sentiment_aggregates(sentiment_aggregates)

print(f"Number of movies with sentiment: {len(sentiment_aggregates)}")
print(f"Number of movies in content_rec: {len(movies_df)}")
print(f"Number of movies in collab_rec: {len(collab_rec.movie_to_idx)}")

# Let's inspect user 1
train_user_ratings_map = {
    uid: group.to_dict(orient="records")
    for uid, group in train_ratings.groupby("userId")
}
u1_train = train_user_ratings_map[1]
rated_mids = {r["movieId"] for r in u1_train}

cf_res = collab_rec.recommend_for_user(1, rated_movie_ids=rated_mids, top_n=20)
print("\nUser 1 - Top 10 CF items and their scores in Content and Sentiment:")
for item in cf_res[:10]:
    mid = item["movie_id"]
    row = movies_df[movies_df["movieId"] == mid].iloc[0]
    # compute content score for this item
    idx = content_rec.movie_id_to_idx.get(mid)
    # content user profile
    c_res = content_rec.recommend_for_user(u1_train, top_n=9999, exclude_rated=False)
    c_map = {x["movie_id"]: x["content_score"] for x in c_res}
    c_score = c_map.get(mid, 0.0)
    sent_meta = sentiment_aggregates.get(mid)
    sent_score = sent_meta.get("aggregate_sentiment_score") if sent_meta else None
    print(f"  CF Item {mid} ({row['title'][:30]}): CF={item['collaborative_score']}, Cont={c_score}, Sent={sent_score}")

hyb_res = hybrid_rec.recommend(1, user_ratings=u1_train, top_n=10, exclude_rated=True)
print("\nUser 1 - Top 10 Hybrid items and their breakdown:")
for item in hyb_res:
    print(f"  Hyb Item {item['movie_id']} ({item['title'][:30]}): Final={item['final_score']}, CF={item['collaborative_score']}, Cont={item['content_score']}, Sent={item['sentiment_score']}, Eff_W={item['effective_weights']}")
