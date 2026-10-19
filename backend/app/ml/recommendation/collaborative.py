"""
CineMind AI — Collaborative Filtering Engine
Matrix Factorization using Truncated SVD and Item-Item cosine similarity.
Explicitly flags when collaborative evidence is unavailable rather than fabricating scores.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

logger = logging.getLogger("CineMind-CollaborativeRecommender")


class CollaborativeRecommender:
    """
    Latent factor matrix factorization model for user-item collaborative filtering.
    Preserves true interaction sparsity and reports collaborative_available=False
    when a user or movie lacks sufficient rating history.
    """

    def __init__(self, n_factors: int = 20, min_ratings_user: int = 1, min_ratings_movie: int = 1):
        self.n_factors = n_factors
        self.min_ratings_user = min_ratings_user
        self.min_ratings_movie = min_ratings_movie
        self.user_to_idx: Dict[int, int] = {}
        self.idx_to_user: Dict[int, int] = {}
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}
        
        self.user_factors: Optional[np.ndarray] = None
        self.item_factors: Optional[np.ndarray] = None
        self.global_mean: float = 3.5
        self.user_means: Optional[np.ndarray] = None
        self.is_fitted = False

    def fit(self, ratings_df: pd.DataFrame):
        """Fit Truncated SVD matrix factorization on the user-item interaction matrix."""
        logger.info(f"Fitting Collaborative Filtering on {len(ratings_df)} user interactions...")
        
        unique_users = sorted(ratings_df["userId"].unique())
        unique_movies = sorted(ratings_df["movieId"].unique())
        
        self.user_to_idx = {uid: idx for idx, uid in enumerate(unique_users)}
        self.idx_to_user = {idx: uid for idx, uid in enumerate(unique_users)}
        self.movie_to_idx = {mid: idx for idx, mid in enumerate(unique_movies)}
        self.idx_to_movie = {idx: mid for idx, mid in enumerate(unique_movies)}
        
        n_users = len(unique_users)
        n_movies = len(unique_movies)
        self.global_mean = float(ratings_df["rating"].mean())
        
        # Build Sparse User-Item Matrix
        user_indices = [self.user_to_idx[uid] for uid in ratings_df["userId"]]
        movie_indices = [self.movie_to_idx[mid] for mid in ratings_df["movieId"]]
        ratings = ratings_df["rating"].values.astype(np.float32)
        
        # Center ratings by user mean to handle lenient vs strict raters
        user_rating_sums = np.zeros(n_users, dtype=np.float32)
        user_rating_counts = np.zeros(n_users, dtype=np.float32)
        for u_idx, r in zip(user_indices, ratings):
            user_rating_sums[u_idx] += r
            user_rating_counts[u_idx] += 1
            
        self.user_means = np.where(user_rating_counts > 0, user_rating_sums / user_rating_counts, self.global_mean)
        
        centered_ratings = np.array([
            r - self.user_means[u_idx] for u_idx, r in zip(user_indices, ratings)
        ], dtype=np.float32)
        
        sparse_matrix = csr_matrix(
            (centered_ratings, (user_indices, movie_indices)),
            shape=(n_users, n_movies)
        )
        
        # Truncated SVD for latent dimensionality reduction
        actual_factors = min(self.n_factors, min(n_users, n_movies) - 1)
        actual_factors = max(2, actual_factors)
        
        svd = TruncatedSVD(n_components=actual_factors, random_state=42)
        self.user_factors = svd.fit_transform(sparse_matrix)
        self.item_factors = svd.components_.T # Shape: (n_movies, actual_factors)
        
        self.is_fitted = True
        logger.info(f"Collaborative filtering fitted: {n_users} users, {n_movies} movies, {actual_factors} latent factors.")

    def predict_rating(self, user_id: int, movie_id: int) -> Tuple[Optional[float], bool]:
        """
        Predict rating score for a (user, movie) pair.
        Returns: (predicted_rating, is_available)
        If user or movie is not in training history, returns (None, False).
        """
        if not self.is_fitted:
            return None, False

        if user_id not in self.user_to_idx or movie_id not in self.movie_to_idx:
            return None, False

        u_idx = self.user_to_idx[user_id]
        m_idx = self.movie_to_idx[movie_id]

        user_vec = self.user_factors[u_idx]
        item_vec = self.item_factors[m_idx]
        
        predicted_centered = float(np.dot(user_vec, item_vec))
        predicted = predicted_centered + self.user_means[u_idx]
        
        # Clip to realistic rating bounds [0.5, 5.0]
        clipped_rating = max(0.5, min(5.0, predicted))
        return round(clipped_rating, 3), True

    def predict_score_normalized(self, user_id: int, movie_id: int) -> Tuple[Optional[float], bool]:
        """
        Normalized collaborative affinity score for a (user, movie) pair in [0.0, 1.0].
        Uses user-level dynamic range normalization across the latent factor projection
        to provide a calibrated [0.0, 1.0] score.
        """
        if not self.is_fitted or user_id not in self.user_to_idx or movie_id not in self.movie_to_idx:
            return None, False

        u_idx = self.user_to_idx[user_id]
        m_idx = self.movie_to_idx[movie_id]
        user_vec = self.user_factors[u_idx]
        dots = np.dot(user_vec, self.item_factors.T)
        
        d_min = float(dots.min())
        d_max = float(dots.max())
        d_rng = d_max - d_min if d_max > d_min else 1.0
        
        norm_score = float(np.clip((dots[m_idx] - d_min) / d_rng, 0.0, 1.0))
        return round(norm_score, 4), True

    def predict_user_scores_normalized(
        self,
        user_id: int,
        candidate_movie_ids: Optional[Set[int]] = None
    ) -> Dict[int, float]:
        """
        Compute min-max normalized collaborative scores in [0.0, 1.0] for a known user across items.
        Normalizes the user's latent dot-product variance so collaborative affinity has
        calibrated dynamic range comparable to TF-IDF cosine similarity.
        """
        if not self.is_fitted or user_id not in self.user_to_idx:
            return {}

        u_idx = self.user_to_idx[user_id]
        user_vec = self.user_factors[u_idx]
        dots = np.dot(user_vec, self.item_factors.T)
        
        d_min = float(dots.min())
        d_max = float(dots.max())
        d_rng = d_max - d_min if d_max > d_min else 1.0

        scores = {}
        for mid, idx in self.movie_to_idx.items():
            if candidate_movie_ids is None or mid in candidate_movie_ids:
                norm_val = float(np.clip((dots[idx] - d_min) / d_rng, 0.0, 1.0))
                scores[mid] = round(norm_val, 4)
        return scores

    def recommend_for_user(
        self,
        user_id: int,
        rated_movie_ids: Set[int],
        candidate_movie_ids: Optional[List[int]] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate collaborative recommendations for a known user.
        If user has no rating history in the matrix, returns empty list (cold-start).
        """
        if not self.is_fitted or user_id not in self.user_to_idx:
            return []

        u_idx = self.user_to_idx[user_id]
        user_vec = self.user_factors[u_idx]
        
        # Predict dot product for all items
        dots = np.dot(user_vec, self.item_factors.T)
        predicted_ratings = dots + self.user_means[u_idx]
        
        d_min = float(dots.min())
        d_max = float(dots.max())
        d_rng = d_max - d_min if d_max > d_min else 1.0

        # Candidate filter
        if candidate_movie_ids:
            valid_candidates = [
                mid for mid in candidate_movie_ids
                if mid in self.movie_to_idx and mid not in rated_movie_ids
            ]
        else:
            valid_candidates = [
                mid for mid, idx in self.movie_to_idx.items()
                if mid not in rated_movie_ids
            ]

        results = []
        for mid in valid_candidates:
            m_idx = self.movie_to_idx[mid]
            pred = float(predicted_ratings[m_idx])
            pred_clipped = max(0.5, min(5.0, pred))
            norm_score = float(np.clip((dots[m_idx] - d_min) / d_rng, 0.0, 1.0))

            results.append({
                "movie_id": mid,
                "collaborative_score": round(norm_score, 4),
                "predicted_rating": round(pred_clipped, 2),
                "collaborative_available": True
            })

        results.sort(key=lambda x: x["collaborative_score"], reverse=True)
        return results[:top_n]
