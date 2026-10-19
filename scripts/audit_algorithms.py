import os
import sys

# Ensure backend in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database.connection import SessionLocal
from app.services.recommendation_service import get_recommendation_service
from app.services.explainability_service import get_explainability_service
from app.database.models import Rating

def main():
    print("=== Auditing CineMind AI Recommendation & Explainability Algorithms ===")
    db = SessionLocal()
    rec_service = get_recommendation_service()
    explain_service = get_explainability_service()

    test_users = [1, 2, 50, 610, 9999]

    for uid in test_users:
        rated_mids = set(r.movie_id for r in db.query(Rating.movie_id).filter(Rating.user_id == uid).all())
        res = rec_service.get_recommendations_for_user(db, user_id=uid, top_n=10)
        items = res["items"]
        rec_mids = [it["movie_id"] for it in items]
        
        # 1. Check duplicate items
        assert len(rec_mids) == len(set(rec_mids)), f"User {uid} has duplicate recommendations: {rec_mids}"
        
        # 2. Check rated-movie exclusion
        leaked_mids = set(rec_mids).intersection(rated_mids)
        assert len(leaked_mids) == 0, f"User {uid} leaked rated movies: {leaked_mids}"
        
        # 3. Check score ranges [0, 1]
        for it in items:
            assert 0.0 <= it["final_score"] <= 1.0, f"Invalid final score {it['final_score']} for movie {it['movie_id']}"
            if it["content_score"] is not None:
                assert 0.0 <= it["content_score"] <= 1.0
            if it["collaborative_score"] is not None:
                assert 0.0 <= it["collaborative_score"] <= 1.0
            if it["sentiment_score"] is not None:
                assert 0.0 <= it["sentiment_score"] <= 1.0

        # 4. Check Explanation consistency for the top-1 recommended movie
        top_movie_id = items[0]["movie_id"]
        exp = explain_service.explain(db, movie_id=top_movie_id, user_id=uid)
        
        # Verify explanation math: final_score = sum(w_i * s_i)
        w = exp["effective_weights"]
        s = exp["scores"]
        expected_score = 0.0
        if s["content_score"] is not None and "content" in w:
            expected_score += w["content"] * s["content_score"]
        if s["collaborative_score"] is not None and "collaborative" in w:
            expected_score += w["collaborative"] * s["collaborative_score"]
        if s["sentiment_score"] is not None and "sentiment" in w:
            expected_score += w["sentiment"] * s["sentiment_score"]

        diff = abs(exp["final_score"] - expected_score)
        assert diff < 1e-3, f"Explanation score mismatch: exp={exp['final_score']} vs calc={expected_score} (diff={diff})"

        print(f"[PASS] User {uid:>4}: rated={len(rated_mids):>4}, cold_start={str(res['is_cold_start']):<5}, "
              f"top_rec='{items[0]['title'][:30]}' (score={items[0]['final_score']:.4f}, exp_diff={diff:.6f})")

    db.close()
    print("=== All Recommendation Algorithm & Explainability Audits PASSED ===")

if __name__ == "__main__":
    main()
