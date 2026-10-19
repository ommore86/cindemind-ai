// CineMind AI TypeScript Type Definitions

export interface Movie {
  movie_id: number;
  title: string;
  genres: string;
  year: number;
  overview?: string;
  avg_rating: number;
  rating_count: number;
  weighted_score: number;
  poster_url?: string;
}

export interface MovieDetail extends Movie {
  tags?: string;
  imdb_id?: string;
  tmdb_id?: string;
  sentiment_score?: number | null;
  sentiment_available: boolean;
  review_count: number;
}

export interface MovieListResponse {
  total: number;
  page: number;
  limit: number;
  pages: number;
  items: Movie[];
}

export interface RecommendationItem {
  movie_id: number;
  title: string;
  genres: string;
  year: number;
  poster_url?: string;
  avg_rating: number;
  rating_count: number;
  weighted_score?: number;
  final_score: number;
  content_score?: number | null;
  collaborative_score?: number | null;
  sentiment_score?: number | null;
  content_available: boolean;
  collaborative_available: boolean;
  sentiment_available: boolean;
  effective_weights: Record<string, number>;
  is_cold_start: boolean;
}

export interface RecommendationResponse {
  user_id?: number | null;
  total_recommendations: number;
  is_cold_start: boolean;
  preferred_genres: string[];
  base_weights: Record<string, number>;
  items: RecommendationItem[];
}

export interface SimilarMovieWatched {
  movie_id: number;
  title: string;
  similarity_score: number;
  user_rating?: number | null;
}

export interface SentimentEvidence {
  analyzed_reviews: number;
  positive_count: number;
  negative_count: number;
  positive_ratio: number;
  average_confidence: number;
  sample_quote?: string | null;
}

export interface ExplanationResponse {
  movie_id: number;
  title: string;
  genres: string[];
  final_score: number;
  scores: {
    content_score?: number | null;
    collaborative_score?: number | null;
    sentiment_score?: number | null;
  };
  effective_weights: Record<string, number>;
  matching_genres: string[];
  shared_keywords?: string[];
  similar_movies_watched: SimilarMovieWatched[];
  sentiment_evidence?: SentimentEvidence | null;
  data_coverage: {
    content_available: boolean;
    collaborative_available: boolean;
    sentiment_available: boolean;
    is_cold_start: boolean;
  };
  user_context: {
    ratings_count: number;
    user_mean_rating: number;
  };
  natural_language_explanation: string;
}

export interface ReviewItem {
  id: number;
  movie_id: number;
  review_id?: string;
  review_text: string;
  ground_truth_sentiment?: string | null;
  predicted_sentiment?: string | null;
  sentiment_confidence?: number | null;
}

export interface MovieSentimentSummary {
  movie_id: number;
  title?: string | null;
  sentiment_available: boolean;
  analyzed_reviews: number;
  positive_count: number;
  negative_count: number;
  positive_ratio: number;
  negative_ratio: number;
  aggregate_sentiment_score?: number | null;
  average_confidence: number;
  recent_reviews: ReviewItem[];
}

export interface SentimentAnalysisResponse {
  text: string;
  label: string;
  confidence: number;
  is_empty: boolean;
}

export interface AnalyticsOverview {
  total_movies: number;
  total_ratings: number;
  total_reviews: number;
  unique_users: number;
  global_average_rating: number;
  spark_pipeline_status: string;
  spark_engine: string;
  last_updated: string;
}

export interface RatingDistributionItem {
  rating: number;
  count: number;
}

export interface GenreDistributionItem {
  genre: string;
  movie_count: number;
  average_rating: number;
}

export interface SentimentAnalyticsResponse {
  total_reviews_analyzed: number;
  positive_reviews: number;
  negative_reviews: number;
  overall_positive_ratio: number;
  top_sentiment_movies: Array<{
    movie_id: number;
    title: string;
    poster_url?: string;
    sentiment_score: number;
    reviews_count: number;
  }>;
  bottom_sentiment_movies: Array<{
    movie_id: number;
    title: string;
    poster_url?: string;
    sentiment_score: number;
    reviews_count: number;
  }>;
}

export interface ModelBenchmarkItem {
  model_name: string;
  display_name: string;
  precision_at_k?: number | null;
  recall_at_k?: number | null;
  ndcg_at_k?: number | null;
  rmse?: number | null;
  mae?: number | null;
}

export interface RecommendationAnalyticsResponse {
  k_value: number;
  sample_size_users: number;
  benchmarks: ModelBenchmarkItem[];
  notes: string[];
}
