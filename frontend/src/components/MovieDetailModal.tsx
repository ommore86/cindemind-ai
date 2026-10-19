import React, { useEffect, useState } from 'react';
import { X, Star, ExternalLink, MessageSquare, ThumbsUp, ThumbsDown, Sparkles, Tag } from 'lucide-react';
import { MovieDetail, MovieSentimentSummary } from '../types';
import { api } from '../services/api';

interface MovieDetailModalProps {
  movieId: number | null;
  onClose: () => void;
  onExplain?: (movieId: number) => void;
}

export const MovieDetailModal: React.FC<MovieDetailModalProps> = ({
  movieId,
  onClose,
  onExplain
}) => {
  const [movie, setMovie] = useState<MovieDetail | null>(null);
  const [sentiment, setSentiment] = useState<MovieSentimentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!movieId) return;

    setLoading(true);
    setError(null);

    Promise.all([
      api.getMovieDetail(movieId),
      api.getMovieSentiment(movieId).catch(() => null)
    ])
      .then(([movieData, sentimentData]) => {
        setMovie(movieData);
        setSentiment(sentimentData);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load movie details');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [movieId]);

  if (!movieId) return null;

  return (
    <div 
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto cursor-pointer"
    >
      <div 
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8 cursor-default"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-30 p-2 rounded-full bg-slate-950/60 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {loading ? (
          <div className="py-24 text-center space-y-3">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm text-slate-400">Loading movie intelligence...</p>
          </div>
        ) : error || !movie ? (
          <div className="p-8 text-center space-y-4">
            <p className="text-rose-400">{error || 'Movie details not available'}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 text-white text-sm"
            >
              Close
            </button>
          </div>
        ) : (
          <div>
            {/* Header / Media Banner */}
            <div className="relative aspect-[16/8] sm:aspect-[16/7] w-full overflow-hidden bg-slate-950">
              <img
                src={movie.poster_url || 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=60'}
                alt={movie.title}
                className="w-full h-full object-cover object-top opacity-50"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/60 to-transparent" />

              <div className="absolute bottom-4 left-6 right-6">
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {movie.genres.split('|').filter(g => g && g !== '(no genres listed)').map((g) => (
                    <span key={g} className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {g}
                    </span>
                  ))}
                  {movie.year > 0 && (
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300">
                      {movie.year}
                    </span>
                  )}
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold text-white font-['Outfit']">
                  {movie.title}
                </h2>
              </div>
            </div>

            {/* Body Info */}
            <div className="p-6 space-y-6">
              {/* Rating Stats Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Average Rating</span>
                  <div className="flex items-center space-x-1.5 mt-0.5">
                    <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                    <span className="text-base font-bold text-white">{movie.avg_rating.toFixed(2)}</span>
                    <span className="text-xs text-slate-500">/ 5.0</span>
                  </div>
                </div>

                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Total Ratings</span>
                  <span className="text-base font-bold text-white mt-0.5 block">{movie.rating_count}</span>
                </div>

                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Bayesian Score</span>
                  <span className="text-base font-bold text-cyan-400 mt-0.5 block">{movie.weighted_score.toFixed(2)}</span>
                </div>

                <div>
                  <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Audience Sentiment</span>
                  <span className={`text-sm font-bold mt-1 block ${
                    sentiment?.sentiment_available
                      ? 'text-emerald-400'
                      : 'text-slate-500'
                  }`}>
                    {sentiment?.sentiment_available 
                      ? `${Math.round((sentiment.aggregate_sentiment_score || 0) * 100)}% Positive`
                      : 'No Reviews'}
                  </span>
                </div>
              </div>

              {/* Overview / Narrative */}
              <div>
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Synopsis & Overview</h4>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {movie.overview || `${movie.title} is a ${movie.genres.replace(/\|/g, ', ')} film.`}
                </p>
              </div>

              {/* Tags */}
              {movie.tags && (
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1">
                    <Tag className="w-3 h-3" />
                    <span>Keywords & Metadata Tags</span>
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {movie.tags.split(' ').map((t, idx) => (
                      <span key={idx} className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700/50">
                        #{t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Audience Reviews & Sentiment */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Verified Movie Reviews ({sentiment?.recent_reviews.length || 0})</span>
                  </h4>
                  {sentiment?.sentiment_available && (
                    <span className="text-xs text-slate-400">
                      Model: DistilBERT SST-2 (Avg Confidence: {Math.round(sentiment.average_confidence * 100)}%)
                    </span>
                  )}
                </div>

                {sentiment && sentiment.recent_reviews.length > 0 ? (
                  <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                    {sentiment.recent_reviews.map((rev) => (
                      <div key={rev.id} className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-xs space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400 font-mono text-[10px]">Review ID: {rev.review_id}</span>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold flex items-center space-x-1 ${
                            rev.predicted_sentiment === 'POSITIVE'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}>
                            {rev.predicted_sentiment === 'POSITIVE' ? (
                              <ThumbsUp className="w-2.5 h-2.5" />
                            ) : (
                              <ThumbsDown className="w-2.5 h-2.5" />
                            )}
                            <span>{rev.predicted_sentiment} ({Math.round((rev.sentiment_confidence || 0) * 100)}%)</span>
                          </span>
                        </div>
                        <p className="text-slate-200 italic">"{rev.review_text}"</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic p-3 rounded-lg bg-slate-950/40 border border-slate-800">
                    No analyzed review text available for this title in the current sample.
                  </p>
                )}
              </div>

              {/* Footer Actions & External Links */}
              <div className="pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-3">
                  {movie.imdb_id && (
                    <a
                      href={`https://www.imdb.com/title/tt${movie.imdb_id.padStart(7, '0')}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-1 text-xs text-amber-400 hover:text-amber-300 transition-colors"
                    >
                      <span>IMDb Profile</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {movie.tmdb_id && (
                    <a
                      href={`https://www.themoviedb.org/movie/${movie.tmdb_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                    >
                      <span>TMDb Page</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>

                {onExplain && (
                  <button
                    onClick={() => {
                      onClose();
                      onExplain(movie.movie_id);
                    }}
                    className="flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 hover:from-amber-400 hover:to-amber-500 transition-all shadow-md shadow-amber-500/20"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Run Explainable AI (XAI)</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
