import sys
import json
import urllib.request
import urllib.parse
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post(path, data):
    url = f"{BASE_URL}{path}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

print("=== CineMind AI End-to-End Functional Verification Suite ===")

# 1. Health Check
st, data = get("/health")
print(f"1. /health: HTTP {st}, status={data.get('status')}, service={data.get('service')}")
assert st == 200 and data.get("status") == "healthy"

# 2. Movie Search & Genre Filter
st, data = get("/api/v1/movies?search=Matrix")
print(f"2a. Search 'Matrix': HTTP {st}, total={data.get('total')}, first={data.get('items', [{}])[0].get('title')}")
assert st == 200 and any("Matrix" in m.get("title", "") for m in data.get("items", []))

st, data = get("/api/v1/movies?genre=Animation&limit=5")
print(f"2b. Genre 'Animation': HTTP {st}, items={len(data.get('items', []))}")
assert st == 200 and all("Animation" in m.get("genres", "") for m in data.get("items", []))

# 3. Personalized Recommendations for User 1
st, data = get("/api/v1/recommendations/1?top_n=10")
recs = data.get("items", [])
print(f"3. Personalized Recs User 1: HTTP {st}, count={len(recs)}, is_cold_start={data.get('is_cold_start')}")
assert st == 200 and len(recs) == 10 and data.get("is_cold_start") is False

# 4. Integrity Checks: No duplicates, valid IDs, non-empty titles, rated movie exclusion
rec_mids = [item["movie_id"] for item in recs]
assert len(rec_mids) == len(set(rec_mids)), "Duplicate movie IDs found in recommendations!"
assert all(item["title"] for item in recs), "Missing movie titles in recommendations!"

# Check rated movie exclusion:
ratings_df = pd.read_csv("data/processed/ratings_cleaned.csv")
user1_rated_mids = set(ratings_df[ratings_df["userId"] == 1]["movieId"].tolist())
overlap = set(rec_mids) & user1_rated_mids
print(f"4. User 1 Rated Movie Exclusion Check: user rated {len(user1_rated_mids)} movies. Overlap with top-10 recs: {overlap}")
assert len(overlap) == 0, f"Error: Recommendation includes already rated movies: {overlap}!"

# Verify weight consistency
base_w = data.get("base_weights", {})
print(f"   Base weights in API: {base_w}")
assert base_w.get("content") == 0.45 and base_w.get("collaborative") == 0.40 and base_w.get("sentiment") == 0.15

# 5. Recommendation Explanations for a returned movie
target_mid = recs[0]["movie_id"]
st, exp = get(f"/api/v1/recommendations/1/{target_mid}/explanation")
print(f"5. Recommendation Explanation for movie {target_mid} ({exp.get('title')}): HTTP {st}")
print(f"   Matching genres: {exp.get('matching_genres')}")
print(f"   Narrative: {exp.get('natural_language_explanation')[:120]}...")
assert st == 200 and exp.get("movie_id") == target_mid
assert exp.get("final_score") is not None
assert len(exp.get("natural_language_explanation", "")) > 20

# 6. Guest Recommendations (Cold Start)
guest_payload = {
    "preferred_genres": ["Sci-Fi", "Action"],
    "seed_movie_ids": [2571], # The Matrix
    "top_n": 5
}
st, guest_res = post("/api/v1/recommendations/guest", guest_payload)
guest_items = guest_res.get("items", [])
print(f"6. Guest Cold-Start Recs: HTTP {st}, items={len(guest_items)}, is_cold_start={guest_res.get('is_cold_start')}")
assert st == 200 and len(guest_items) == 5
assert all(item["is_cold_start"] for item in guest_items)

# 7. Live Sentiment Analysis (Positive and Negative)
pos_payload = {"text": "An absolute cinematic masterpiece with breathtaking visual effects and profound performances."}
st, pos_res = post("/api/v1/sentiment/analyze", pos_payload)
print(f"7a. Sentiment Positive Text: HTTP {st}, label={pos_res.get('label')}, confidence={pos_res.get('confidence')}")
assert st == 200 and pos_res.get("label") == "POSITIVE" and pos_res.get("confidence") > 0.90

neg_payload = {"text": "A dreadful failure with terrible script, awful pacing, and uninspired acting."}
st, neg_res = post("/api/v1/sentiment/analyze", neg_payload)
print(f"7b. Sentiment Negative Text: HTTP {st}, label={neg_res.get('label')}, confidence={neg_res.get('confidence')}")
assert st == 200 and neg_res.get("label") == "NEGATIVE" and neg_res.get("confidence") > 0.90

# 8. Analytics & Benchmarks Verification
st, b_data = get("/api/v1/analytics/recommendations")
print(f"8. Analytics Benchmarks: HTTP {st}, sample_users={b_data.get('sample_size_users')}")
bm_map = {b["model_name"]: b for b in b_data.get("benchmarks", [])}
for m_name in ["content_based", "collaborative", "hybrid"]:
    bm = bm_map.get(m_name, {})
    print(f"   {m_name:15}: P@10={bm.get('precision_at_k')}, R@10={bm.get('recall_at_k')}, NDCG@10={bm.get('ndcg_at_k')}")

# Match against evaluation_report.json
with open("data/processed/evaluation_report.json", "r") as f:
    rep = json.load(f)
assert bm_map["hybrid"]["precision_at_k"] == rep["models"]["hybrid"]["precision_at_k"]
assert bm_map["hybrid"]["recall_at_k"] == rep["models"]["hybrid"]["recall_at_k"]
assert bm_map["hybrid"]["ndcg_at_k"] == rep["models"]["hybrid"]["ndcg_at_k"]
print("   Verification: Database benchmarks MATCH evaluation_report.json exactly!")

# 9. Additional Analytics Endpoints
for ep in ["/api/v1/analytics/overview", "/api/v1/analytics/ratings", "/api/v1/analytics/genres", "/api/v1/analytics/sentiment"]:
    st, d = get(ep)
    print(f"9. {ep:32}: HTTP {st}")
    assert st == 200

print("\n=== ALL VERIFICATION CHECKS PASSED SUCCESSFULLY ===")
