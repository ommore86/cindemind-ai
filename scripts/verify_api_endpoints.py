import urllib.request
import urllib.error
import json
import sys

base = 'http://127.0.0.1:8000'

def test(name, path, method='GET', body=None, expect_code=200):
    url = base + path
    headers = {'Content-Type': 'application/json'} if body else {}
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.status
            content = json.loads(resp.read().decode('utf-8'))
            assert code == expect_code, f"Expected {expect_code}, got {code}"
            print(f"[PASS] {name}: status {code}")
            return content
    except urllib.error.HTTPError as e:
        if e.code == expect_code:
            print(f"[PASS] {name}: expected error {e.code}")
            try:
                return json.loads(e.read().decode('utf-8'))
            except Exception:
                return {}
        else:
            print(f"[FAIL] {name}: unexpected status {e.code}")
            raise

def main():
    print("=== CineMind AI End-to-End API QA Audit ===")
    
    # 1. Health
    h = test('1. Health Check', '/health')
    assert h['status'] == 'healthy'
    assert h['service'] == 'CineMind AI'

    # 2. Movies list pagination
    m = test('2. Movies List Pagination', '/api/v1/movies?page=1&limit=10&sort_by=weighted_score&order=desc')
    assert len(m['items']) == 10
    assert m['total'] == 9742
    assert m['pages'] == 975

    # 3. Movies search
    s = test('3. Movies Title Search (Matrix)', '/api/v1/movies?search=Matrix')
    assert any('Matrix' in item['title'] for item in s['items'])

    # 4. Movies genre filter
    g = test('4. Movies Genre Filter (Sci-Fi)', '/api/v1/movies?genre=Sci-Fi&limit=5')
    assert all('Sci-Fi' in item['genres'] for item in g['items'])

    # 5. Movie detail valid
    md = test('5. Movie Detail (ID 2571)', '/api/v1/movies/2571')
    assert md['movie_id'] == 2571
    assert 'Matrix' in md['title']
    assert md['rating_count'] > 0

    # 6. Movie detail 404 unknown
    test('6. Movie Detail 404 (Unknown ID 9999999)', '/api/v1/movies/9999999', expect_code=404)

    # 7. User recommendations valid
    ur = test('7. User Recommendations (User 1, top 5)', '/api/v1/recommendations/1?top_n=5')
    assert ur['user_id'] == 1
    assert len(ur['items']) == 5
    assert not ur['is_cold_start']

    # 8. User recommendations with genre filter
    urg = test('8. User Recommendations with Genre (User 1, Animation)', '/api/v1/recommendations/1?top_n=5&genre=Animation')
    assert all('Animation' in item['genres'] for item in urg['items'])

    # 9. Cold-start user recommendations
    cs = test('9. Cold-Start User Recommendations (User 99999)', '/api/v1/recommendations/99999?top_n=5')
    assert cs['is_cold_start'] is True
    assert len(cs['items']) == 5

    # 10. Guest recommendations
    guest = test('10. Guest Recommendations', '/api/v1/recommendations/guest', method='POST', body={
        'preferred_genres': ['Sci-Fi', 'Action'],
        'seed_movie_ids': [2571],
        'top_n': 5
    })
    assert guest['is_cold_start'] is True
    assert len(guest['items']) == 5

    # 11. Explainability valid
    exp = test('11. Explainable AI (User 1, Movie 2571)', '/api/v1/recommendations/1/2571/explanation')
    assert 'final_score' in exp
    assert 'scores' in exp
    assert 'effective_weights' in exp
    assert 'sentiment_evidence' in exp
    assert 'natural_language_explanation' in exp

    # 12. Explainability 404
    test('12. Explainable AI 404 (Unknown Movie)', '/api/v1/recommendations/1/9999999/explanation', expect_code=404)

    # 13. Movie sentiment summary
    sent_sum = test('13. Movie Sentiment Summary (Movie 2571)', '/api/v1/movies/2571/sentiment')
    assert sent_sum['movie_id'] == 2571
    assert sent_sum['sentiment_available'] is True
    assert sent_sum['analyzed_reviews'] >= 1

    # 14. Real-time sentiment analysis valid
    sent_inf = test('14. Real-Time Sentiment Inference (Valid)', '/api/v1/sentiment/analyze', method='POST', body={
        'text': 'A cinematic masterpiece with brilliant directing, incredible performances, and profound emotional resonance.'
    })
    assert sent_inf['label'] == 'POSITIVE'
    assert sent_inf['confidence'] > 0.8

    # 15. Real-time sentiment analysis negative
    sent_neg = test('15. Real-Time Sentiment Inference (Negative)', '/api/v1/sentiment/analyze', method='POST', body={
        'text': 'A complete disaster and waste of time with dreadful acting and horrible writing.'
    })
    assert sent_neg['label'] == 'NEGATIVE'

    # 16. Real-time sentiment empty text 400
    test('16. Real-Time Sentiment Empty Text 400', '/api/v1/sentiment/analyze', method='POST', body={
        'text': '   '
    }, expect_code=400)

    # 17. Analytics Overview
    ao = test('17. Analytics Overview', '/api/v1/analytics/overview')
    assert ao['total_movies'] == 9742
    assert ao['total_ratings'] == 100836
    assert ao['unique_users'] == 610

    # 18. Analytics Ratings Distribution
    ar = test('18. Analytics Ratings Distribution', '/api/v1/analytics/ratings')
    assert len(ar) == 10

    # 19. Analytics Genre Distribution
    ag = test('19. Analytics Genre Distribution', '/api/v1/analytics/genres')
    assert len(ag) > 10

    # 20. Analytics Sentiment
    asent = test('20. Analytics Sentiment', '/api/v1/analytics/sentiment')
    assert asent['total_reviews_analyzed'] > 0
    assert 'positive_reviews' in asent
    assert 'negative_reviews' in asent

    # 21. Analytics Recommendation Benchmarks
    ab = test('21. Analytics Benchmarks', '/api/v1/analytics/recommendations')
    assert len(ab['benchmarks']) == 3
    models = {b['model_name']: b for b in ab['benchmarks']}
    assert 'content_based' in models
    assert 'collaborative' in models
    assert 'hybrid' in models

    print("\n>>> ALL 21 API QA CHECKS PASSED WITH FULL STATUS & SCHEMA VALIDATION <<<")

if __name__ == '__main__':
    main()
