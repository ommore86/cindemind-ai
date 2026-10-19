// CineMind AI — Centralized Typed API Client

import {
  Movie,
  MovieDetail,
  MovieListResponse,
  RecommendationResponse,
  ExplanationResponse,
  MovieSentimentSummary,
  SentimentAnalysisResponse,
  AnalyticsOverview,
  RatingDistributionItem,
  GenreDistributionItem,
  SentimentAnalyticsResponse,
  RecommendationAnalyticsResponse
} from '../types';

const rawEnvUrl = (import.meta as any).env?.VITE_API_BASE_URL?.trim();
const cleanUrl = rawEnvUrl ? rawEnvUrl.replace(/\/+$/, '') : '';

export const API_BASE = cleanUrl
  ? (cleanUrl.endsWith('/api/v1') ? cleanUrl : `${cleanUrl}/api/v1`)
  : 'http://localhost:8000/api/v1';

export const ROOT_BASE = cleanUrl
  ? (cleanUrl.endsWith('/api/v1') ? cleanUrl.slice(0, -7) : cleanUrl)
  : 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    });

    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err: any) {
    // If connection to localhost failed, attempt fallback to 127.0.0.1 (resolves Windows IPv6 ::1 issues)
    if (url.includes('localhost:8000')) {
      const fallbackUrl = url.replace('localhost:8000', '127.0.0.1:8000');
      try {
        const fallbackRes = await fetch(fallbackUrl, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {})
          }
        });
        if (fallbackRes.ok) {
          return await fallbackRes.json();
        }
      } catch (_) {}
    }
    console.error(`API Request failed for [${url}]:`, err);
    throw err;
  }
}

export const api = {
  // Movies
  getMovies: (params: {
    page?: number;
    limit?: number;
    search?: string;
    genre?: string;
    sort_by?: string;
    order?: string;
  } = {}): Promise<MovieListResponse> => {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page.toString());
    if (params.limit) query.append('limit', params.limit.toString());
    if (params.search) query.append('search', params.search);
    if (params.genre && params.genre !== 'All') query.append('genre', params.genre);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.order) query.append('order', params.order);

    return request<MovieListResponse>(`/movies?${query.toString()}`);
  },

  getMovieDetail: (movieId: number): Promise<MovieDetail> => {
    return request<MovieDetail>(`/movies/${movieId}`);
  },

  // Recommendations
  getUserRecommendations: (
    userId: number,
    topN: number = 10,
    genre?: string
  ): Promise<RecommendationResponse> => {
    const query = new URLSearchParams();
    query.append('top_n', topN.toString());
    if (genre && genre !== 'All') query.append('genre', genre);

    return request<RecommendationResponse>(`/recommendations/${userId}?${query.toString()}`);
  },

  getGuestRecommendations: (payload: {
    preferred_genres: string[];
    seed_movie_ids?: number[];
    top_n?: number;
  }): Promise<RecommendationResponse> => {
    return request<RecommendationResponse>('/recommendations/guest', {
      method: 'POST',
      body: JSON.stringify({
        preferred_genres: payload.preferred_genres,
        seed_movie_ids: payload.seed_movie_ids || [],
        top_n: payload.top_n || 10
      })
    });
  },

  // Explainability
  getExplanation: (
    userId: number,
    movieId: number,
    genre?: string
  ): Promise<ExplanationResponse> => {
    const query = new URLSearchParams();
    if (genre && genre !== 'All') query.append('genre', genre);
    return request<ExplanationResponse>(`/recommendations/${userId}/${movieId}/explanation?${query.toString()}`);
  },

  // Sentiment
  getMovieSentiment: (movieId: number): Promise<MovieSentimentSummary> => {
    return request<MovieSentimentSummary>(`/movies/${movieId}/sentiment`);
  },

  analyzeSentiment: (text: string, movieId?: number): Promise<SentimentAnalysisResponse> => {
    return request<SentimentAnalysisResponse>('/sentiment/analyze', {
      method: 'POST',
      body: JSON.stringify({ text, movie_id: movieId })
    });
  },

  // Analytics
  getAnalyticsOverview: (): Promise<AnalyticsOverview> => {
    return request<AnalyticsOverview>('/analytics/overview');
  },

  getRatingsDistribution: (): Promise<RatingDistributionItem[]> => {
    return request<RatingDistributionItem[]>('/analytics/ratings');
  },

  getGenreDistribution: (): Promise<GenreDistributionItem[]> => {
    return request<GenreDistributionItem[]>('/analytics/genres');
  },

  getSentimentAnalytics: (): Promise<SentimentAnalyticsResponse> => {
    return request<SentimentAnalyticsResponse>('/analytics/sentiment');
  },

  getRecommendationBenchmarks: (): Promise<RecommendationAnalyticsResponse> => {
    return request<RecommendationAnalyticsResponse>('/analytics/recommendations');
  },

  // Health
  checkHealth: async (): Promise<boolean> => {
    // 1. Check primary ROOT_BASE/health
    try {
      const res = await fetch(`${ROOT_BASE}/health`);
      if (res.ok) return true;
    } catch {}

    // 2. Check API_BASE/health
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) return true;
    } catch {}

    // 3. Fallback for local dev if bound to 127.0.0.1
    if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
      try {
        const res = await fetch('http://127.0.0.1:8000/health');
        if (res.ok) return true;
      } catch {}
      try {
        const res = await fetch('http://localhost:8000/health');
        if (res.ok) return true;
      } catch {}
    }

    return false;
  }
};
