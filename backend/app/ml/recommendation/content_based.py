"""
CineMind AI — Content-Based Movie Recommendation Engine
Utilizes TF-IDF vectorization and Cosine Similarity on rich movie metadata
(genres, overview, tags, title) with genre-filtering and preference weighting.
"""

import logging
from typing import List, Dict, Any, Optional, Set
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("CineMind-ContentRecommender")


class ContentBasedRecommender:
    """
    Content-Based Filtering model utilizing TF-IDF representations.
    Precomputes and caches sparse TF-IDF feature matrices and movie index lookups.
    """

    def __init__(self, max_features: int = 5000):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=max_features,
            ngram_range=(1, 2)
        )
        self.tfidf_matrix = None
        self.movie_df: Optional[pd.DataFrame] = None
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        self.feature_names = np.array([])
        self.is_fitted = False

    def fit(self, movies_df: pd.DataFrame):
        """Fit the TF-IDF vectorizer on movie content text and cache mappings."""
        logger.info(f"Fitting Content-Based Recommender on {len(movies_df)} movies...")
        self.movie_df = movies_df.copy().reset_index(drop=True)
        
        # Build index lookups
        self.movie_id_to_idx = {int(row["movieId"]): idx for idx, row in self.movie_df.iterrows()}
        self.idx_to_movie_id = {idx: int(row["movieId"]) for idx, row in self.movie_df.iterrows()}
        
        # Prepare content string
        content_corpus = self.movie_df["content_text"].fillna("").astype(str).tolist()
        self.tfidf_matrix = self.vectorizer.fit_transform(content_corpus)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())
        self.is_fitted = True
        logger.info(f"TF-IDF matrix built with shape {self.tfidf_matrix.shape}.")

    def get_similar_movies(
        self,
        movie_id: int,
        top_n: int = 10,
        genre_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Compute top-N most similar movies to a given movie_id based on cosine similarity.
        """
        if not self.is_fitted or self.movie_df is None:
            raise ValueError("Recommender must be fitted before calling get_similar_movies")

        if movie_id not in self.movie_id_to_idx:
            logger.warning(f"Movie ID {movie_id} not found in content catalog.")
            return []

        target_idx = self.movie_id_to_idx[movie_id]
        target_vec = self.tfidf_matrix[target_idx]
        
        # Cosine similarity against all movies
        similarities = cosine_similarity(target_vec, self.tfidf_matrix).flatten()
        
        # Filter and rank
        ranked_indices = np.argsort(-similarities)
        results = []

        for idx in ranked_indices:
            if idx == target_idx:
                continue
            
            mid = self.idx_to_movie_id[idx]
            row = self.movie_df.iloc[idx]
            sim_score = float(similarities[idx])
            
            # Apply genre filter if provided
            if genre_filter:
                movie_genres = str(row.get("genres", "")).lower()
                if genre_filter.lower() not in movie_genres:
                    continue

            # Identify top shared TF-IDF terms for explainability
            shared_terms = self._get_shared_keywords(target_idx, idx)

            results.append({
                "movie_id": mid,
                "title": row.get("title", ""),
                "genres": row.get("genres", ""),
                "year": int(row.get("year", 0)),
                "content_score": round(sim_score, 4),
                "similarity_score": round(sim_score, 4),
                "shared_keywords": shared_terms,
                "avg_rating": float(row.get("avg_rating", 0.0)),
                "rating_count": int(row.get("rating_count", 0)),
                "poster_url": row.get("poster_url", "")
            })

            if len(results) >= top_n:
                break

        return results

    def recommend_for_user(
        self,
        user_ratings: List[Dict[str, Any]],
        preferred_genres: Optional[List[str]] = None,
        top_n: int = 10,
        exclude_rated: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized content-based recommendations based on user's rating profile.
        Constructs a weighted user preference vector from highly-rated movies (rating >= 3.5).
        """
        if not self.is_fitted or self.movie_df is None:
            raise ValueError("Recommender must be fitted before generating recommendations.")

        rated_mids = {r["movieId"] for r in user_ratings if "movieId" in r}
        
        # Build user profile vector
        user_vector = np.zeros((1, self.tfidf_matrix.shape[1]))
        total_weight = 0.0
        influential_movies = []

        for r in user_ratings:
            mid = r["movieId"]
            rating = float(r.get("rating", 3.0))
            if mid in self.movie_id_to_idx and rating >= 3.0:
                idx = self.movie_id_to_idx[mid]
                # Center around 3.0 so higher ratings have positive weight
                weight = rating - 2.5
                user_vector += weight * self.tfidf_matrix[idx].toarray()
                total_weight += weight
                influential_movies.append((mid, weight))

        # If user has no ratings or all low ratings, fallback to preferred genres vector
        if total_weight > 0:
            user_vector /= total_weight
        else:
            # Cold-start profile using preferred genres
            if preferred_genres:
                genre_text = " ".join(preferred_genres)
                user_vector = self.vectorizer.transform([genre_text]).toarray()
            else:
                # Return highest weighted movies as popular fallback
                top_pop = self.movie_df.sort_values(by="weighted_score", ascending=False).head(top_n)
                return [
                    {
                        "movie_id": int(row["movieId"]),
                        "title": row["title"],
                        "genres": row["genres"],
                        "year": int(row["year"]),
                        "content_score": round(float(row["weighted_score"]) / 5.0, 4),
                        "avg_rating": float(row["avg_rating"]),
                        "rating_count": int(row["rating_count"]),
                        "is_cold_start": True
                    }
                    for _, row in top_pop.iterrows()
                ]

        # Compute cosine similarity between user profile vector and all candidate movies
        sim_scores = cosine_similarity(user_vector, self.tfidf_matrix).flatten()
        ranked_indices = np.argsort(-sim_scores)

        results = []
        for idx in ranked_indices:
            mid = self.idx_to_movie_id[idx]
            if exclude_rated and mid in rated_mids:
                continue

            row = self.movie_df.iloc[idx]
            sim = float(sim_scores[idx])

            # Genre filter boost/filter
            if preferred_genres:
                row_genres = str(row.get("genres", "")).lower()
                matches_pref = any(pg.lower() in row_genres for pg in preferred_genres)
                if not matches_pref:
                    continue

            results.append({
                "movie_id": mid,
                "title": row.get("title", ""),
                "genres": row.get("genres", ""),
                "year": int(row.get("year", 0)),
                "content_score": round(max(0.0, min(1.0, sim)), 4),
                "avg_rating": float(row.get("avg_rating", 0.0)),
                "rating_count": int(row.get("rating_count", 0)),
                "is_cold_start": len(user_ratings) == 0
            })

            if len(results) >= top_n:
                break

        return results

    def _get_shared_keywords(self, idx1: int, idx2: int, top_k: int = 4) -> List[str]:
        """Find overlapping high-importance TF-IDF terms between two movies."""
        vec1 = self.tfidf_matrix[idx1].toarray().flatten()
        vec2 = self.tfidf_matrix[idx2].toarray().flatten()
        overlap = vec1 * vec2
        top_indices = np.argsort(-overlap)[:top_k]
        return [self.feature_names[i] for i in top_indices if overlap[i] > 0]
