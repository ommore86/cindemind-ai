import React, { useState } from 'react';
import { Star, Sparkles, MessageSquare, Brain, Eye } from 'lucide-react';
import { Movie, RecommendationItem } from '../types';

interface MovieCardProps {
  movie: Movie | RecommendationItem;
  onSelectMovie?: (movieId: number) => void;
  onExplain?: (movieId: number) => void;
  showRecommendationDetails?: boolean;
}

export const MovieCard: React.FC<MovieCardProps> = ({
  movie,
  onSelectMovie,
  onExplain,
  showRecommendationDetails = false
}) => {
  const [imageError, setImageError] = useState(false);
  const recItem = showRecommendationDetails ? (movie as RecommendationItem) : null;

  const genresList = movie.genres
    ? movie.genres.split('|').filter(g => g && g !== '(no genres listed)').slice(0, 3)
    : [];

  const posterSrc = (!imageError && movie.poster_url)
    ? movie.poster_url
    : `https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60`;

  return (
    <div className="group relative rounded-xl overflow-hidden bg-slate-900/60 border border-slate-800/80 hover:border-amber-500/40 transition-all duration-300 hover:shadow-xl hover:shadow-amber-500/10 flex flex-col justify-between">
      {/* Top Banner for Recommendation Score */}
      {recItem && (
        <div className="absolute top-2 left-2 right-2 z-20 flex items-center justify-between pointer-events-none">
          <div className="flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-bold bg-slate-950/80 backdrop-blur-md border border-amber-500/40 text-amber-400 shadow-md">
            <Sparkles className="w-3 h-3 text-amber-400" />
            <span>Score: {Math.round(recItem.final_score * 100)}%</span>
          </div>

          {recItem.is_cold_start && (
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-cyan-950/80 border border-cyan-500/30 text-cyan-300">
              Cold-Start
            </span>
          )}
        </div>
      )}

      {/* Poster Media */}
      <div 
        className="relative aspect-[2/3] w-full overflow-hidden bg-slate-950 cursor-pointer"
        onClick={() => onSelectMovie && onSelectMovie(movie.movie_id)}
      >
        <img
          src={posterSrc}
          alt={movie.title}
          onError={() => setImageError(true)}
          className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-500 opacity-90 group-hover:opacity-100"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent opacity-80 group-hover:opacity-60 transition-opacity" />

        {/* Hover quick overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-slate-950/40 backdrop-blur-[2px]">
          <button 
            onClick={(e) => {
              e.stopPropagation();
              onSelectMovie && onSelectMovie(movie.movie_id);
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 text-white text-xs font-semibold border border-slate-700 hover:border-amber-400 transition-colors shadow-lg"
          >
            <Eye className="w-3.5 h-3.5 text-amber-400" />
            <span>View Details</span>
          </button>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
        <div>
          {/* Year & Rating */}
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>{movie.year > 0 ? movie.year : 'Classic'}</span>
            <div className="flex items-center space-x-1 text-amber-400 font-medium">
              <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
              <span>{movie.avg_rating > 0 ? movie.avg_rating.toFixed(1) : 'Unrated'}</span>
              <span className="text-[10px] text-slate-500">({movie.rating_count})</span>
            </div>
          </div>

          {/* Title */}
          <h3 
            onClick={() => onSelectMovie && onSelectMovie(movie.movie_id)}
            className="font-semibold text-sm text-slate-100 line-clamp-1 group-hover:text-amber-400 cursor-pointer transition-colors"
            title={movie.title}
          >
            {movie.title}
          </h3>

          {/* Genre Badges */}
          <div className="flex flex-wrap gap-1 mt-2">
            {genresList.map((g) => (
              <span
                key={g}
                className="text-[10px] px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700/50"
              >
                {g}
              </span>
            ))}
          </div>
        </div>

        {/* Component Scores Breakdown (For recommendations) */}
        {recItem && (
          <div className="pt-2 border-t border-slate-800/60 space-y-1.5">
            <div className="grid grid-cols-3 gap-1 text-[10px] text-center font-mono">
              <div className="bg-slate-950/60 p-1 rounded border border-slate-800">
                <span className="text-slate-400 block text-[9px]">Content</span>
                <span className="text-cyan-400 font-semibold">
                  {recItem.content_score != null ? `${Math.round(recItem.content_score * 100)}%` : '—'}
                </span>
              </div>
              <div className="bg-slate-950/60 p-1 rounded border border-slate-800">
                <span className="text-slate-400 block text-[9px]">Collab</span>
                <span className="text-purple-400 font-semibold">
                  {recItem.collaborative_score != null ? `${Math.round(recItem.collaborative_score * 100)}%` : 'N/A'}
                </span>
              </div>
              <div className="bg-slate-950/60 p-1 rounded border border-slate-800">
                <span className="text-slate-400 block text-[9px]">Sentiment</span>
                <span className="text-emerald-400 font-semibold">
                  {recItem.sentiment_score != null ? `${Math.round(recItem.sentiment_score * 100)}%` : 'N/A'}
                </span>
              </div>
            </div>

            {/* Explainable AI Trigger Button */}
            {onExplain && (
              <button
                onClick={() => onExplain(movie.movie_id)}
                className="w-full mt-2 flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition-all duration-200"
              >
                <Brain className="w-3.5 h-3.5" />
                <span>Why this movie?</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
