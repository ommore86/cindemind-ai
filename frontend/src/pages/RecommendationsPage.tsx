import React, { useEffect, useState } from 'react';
import { Sparkles, User, Filter, Sliders, RefreshCw, AlertCircle, Info, Brain, Film } from 'lucide-react';
import { MovieCard } from '../components/MovieCard';
import { ExplanationModal } from '../components/ExplanationModal';
import { MovieDetailModal } from '../components/MovieDetailModal';
import { RecommendationResponse, RecommendationItem } from '../types';
import { api } from '../services/api';

const USER_PRESETS = [
  { id: 1, label: 'User 1: Sci-Fi & Action Fan', genres: ['Sci-Fi', 'Action'] },
  { id: 2, label: 'User 2: Crime & Drama Aficionado', genres: ['Crime', 'Drama'] },
  { id: 3, label: 'User 3: Family & Animation Lover', genres: ['Animation', 'Children'] },
  { id: 4, label: 'User 4: Mind-Bending Thrillers', genres: ['Mystery', 'Thriller'] },
  { id: 5, label: 'User 5: Mainstream Cinephile', genres: ['Adventure', 'Action'] },
];

const GENRE_CHIPS = ['Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Drama', 'Horror', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller'];

interface RecommendationsPageProps {
  initialMovieIdToExplain?: number | null;
}

export const RecommendationsPage: React.FC<RecommendationsPageProps> = ({
  initialMovieIdToExplain = null
}) => {
  const [selectedUserId, setSelectedUserId] = useState<number>(1);
  const [customUserId, setCustomUserId] = useState<string>('1');
  const [isGuestMode, setIsGuestMode] = useState<boolean>(false);
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [topN, setTopN] = useState<number>(12);

  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [explainMovieId, setExplainMovieId] = useState<number | null>(initialMovieIdToExplain);
  const [detailMovieId, setDetailMovieId] = useState<number | null>(null);

  const fetchRecommendations = () => {
    setLoading(true);
    setError(null);

    const genreParam = selectedGenres.length > 0 ? selectedGenres.join(',') : undefined;

    if (isGuestMode) {
      api.getGuestRecommendations({
        preferred_genres: selectedGenres,
        seed_movie_ids: [1, 260, 2571], // default seeds
        top_n: topN
      })
        .then((data) => setRecommendations(data))
        .catch((err) => setError(err.message || 'Failed to fetch guest recommendations.'))
        .finally(() => setLoading(false));
    } else {
      const uid = parseInt(customUserId) || selectedUserId || 1;
      api.getUserRecommendations(uid, topN, genreParam)
        .then((data) => setRecommendations(data))
        .catch((err) => setError(err.message || 'Failed to fetch personalized recommendations.'))
        .finally(() => setLoading(false));
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [selectedUserId, isGuestMode, topN]);

  const toggleGenre = (genre: string) => {
    setSelectedGenres(prev =>
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    );
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Control Configuration Bar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white font-['Outfit'] flex items-center space-x-2">
              <Sparkles className="w-6 h-6 text-amber-400" />
              <span>Hybrid Recommendation Engine</span>
            </h2>
            <p className="text-xs text-slate-400">
              Blends TF-IDF Content Vector Space (45%), SVD Collaborative Latent Matrix (40%), and DistilBERT Sentiment (15%)
            </p>
          </div>

          <button
            onClick={fetchRecommendations}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-amber-500 text-slate-950 hover:bg-amber-400 disabled:opacity-50 transition-colors shadow-md shadow-amber-500/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Generate Recommendations</span>
          </button>
        </div>

        {/* User Persona & Mode Toggles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-800/80">
          {/* Persona Presets */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              User Profile Mode
            </label>
            <div className="flex rounded-xl bg-slate-950 border border-slate-800 p-1">
              <button
                onClick={() => setIsGuestMode(false)}
                className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  !isGuestMode
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Known User (MovieLens)
              </button>
              <button
                onClick={() => setIsGuestMode(true)}
                className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                  isGuestMode
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Guest (Cold-Start)
              </button>
            </div>
          </div>

          {/* User Selector */}
          {!isGuestMode ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Select Profile Persona
              </label>
              <select
                value={selectedUserId}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  setSelectedUserId(val);
                  setCustomUserId(val.toString());
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500 cursor-pointer"
              >
                {USER_PRESETS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Cold-Start Strategy
              </label>
              <div className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] text-cyan-300">
                Dynamic weight redistribution: collaborative weight &rarr; content & sentiment.
              </div>
            </div>
          )}

          {/* Top-N Recommendations */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <span>Results Count</span>
              <span className="text-amber-400 font-mono">Top {topN}</span>
            </div>
            <div className="flex items-center space-x-2 pt-1">
              {[6, 12, 18, 24].map((n) => (
                <button
                  key={n}
                  onClick={() => setTopN(n)}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-mono font-bold transition-colors ${
                    topN === n
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Preferred Genre Filters */}
        <div className="space-y-2 pt-2 border-t border-slate-800/80">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Optional Genre Biasing / Filter
            </label>
            {selectedGenres.length > 0 && (
              <button
                onClick={() => setSelectedGenres([])}
                className="text-[11px] text-slate-500 hover:text-slate-300 underline"
              >
                Clear Filters
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {GENRE_CHIPS.map((g) => {
              const active = selectedGenres.includes(g);
              return (
                <button
                  key={g}
                  onClick={() => toggleGenre(g)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                    active
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
                      : 'bg-slate-950/80 text-slate-400 border border-slate-800 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {g}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Model Status Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs px-2">
        <div className="flex items-center space-x-2 text-slate-400">
          <span>Active Mode:</span>
          <span className="font-semibold text-white">
            {recommendations?.is_cold_start ? 'Cold-Start / Content Prior' : `User #${recommendations?.user_id} Hybrid Profile`}
          </span>
          <span className="text-slate-600">•</span>
          <span>Base Weights:</span>
          <span className="font-mono text-cyan-400">Content 45%</span>
          <span className="font-mono text-purple-400">Collab 40%</span>
          <span className="font-mono text-emerald-400">Sentiment 15%</span>
        </div>

        <span className="text-slate-400 font-mono">
          {recommendations?.total_recommendations || 0} Ranked Recommendations
        </span>
      </div>

      {/* Recommendations Cards Grid */}
      {loading ? (
        <div className="py-32 text-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Calculating cosine similarity and latent matrix dot products...</p>
        </div>
      ) : error ? (
        <div className="p-8 text-center glass-panel rounded-2xl border border-rose-500/30 text-rose-400 space-y-2">
          <AlertCircle className="w-8 h-8 mx-auto" />
          <p className="font-semibold">{error}</p>
        </div>
      ) : recommendations?.items.length === 0 ? (
        <div className="p-16 text-center glass-panel rounded-2xl border border-slate-800 space-y-3">
          <Film className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-base text-slate-300 font-semibold">No recommendations found</p>
          <p className="text-xs text-slate-500">Try removing restrictive genre filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {recommendations?.items.map((item) => (
            <MovieCard
              key={item.movie_id}
              movie={item}
              onSelectMovie={(id) => setDetailMovieId(id)}
              onExplain={(id) => setExplainMovieId(id)}
              showRecommendationDetails={true}
            />
          ))}
        </div>
      )}

      {/* Explainable AI Modal */}
      <ExplanationModal
        movieId={explainMovieId}
        userId={isGuestMode ? null : (parseInt(customUserId) || selectedUserId)}
        selectedGenre={selectedGenres.join(',')}
        onClose={() => setExplainMovieId(null)}
      />

      {/* Movie Details Modal */}
      <MovieDetailModal
        movieId={detailMovieId}
        onClose={() => setDetailMovieId(null)}
        onExplain={(id) => setExplainMovieId(id)}
      />
    </div>
  );
};
