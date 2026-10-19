import React, { useEffect, useState } from 'react';
import { Search, Filter, ArrowUpDown, ChevronLeft, ChevronRight, SlidersHorizontal, Film } from 'lucide-react';
import { MovieCard } from '../components/MovieCard';
import { MovieDetailModal } from '../components/MovieDetailModal';
import { Movie } from '../types';
import { api } from '../services/api';

const GENRES = [
  'All',
  'Action',
  'Adventure',
  'Animation',
  'Children',
  'Comedy',
  'Crime',
  'Drama',
  'Fantasy',
  'Horror',
  'Mystery',
  'Romance',
  'Sci-Fi',
  'Thriller',
  'War'
];

interface ExplorerPageProps {
  onExplainMovie?: (movieId: number) => void;
}

export const ExplorerPage: React.FC<ExplorerPageProps> = ({ onExplainMovie }) => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [limit] = useState(18);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('All');
  const [sortBy, setSortBy] = useState('weighted_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [loading, setLoading] = useState(true);

  const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null);

  // Fetch movies on criteria change
  useEffect(() => {
    setLoading(true);
    api.getMovies({
      page,
      limit,
      search: searchTerm.trim() || undefined,
      genre: selectedGenre !== 'All' ? selectedGenre : undefined,
      sort_by: sortBy,
      order: sortOrder
    })
      .then((res) => {
        setMovies(res.items);
        setTotal(res.total);
        setPages(res.pages);
      })
      .catch((err) => {
        console.error('Error fetching movies:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [page, limit, searchTerm, selectedGenre, sortBy, sortOrder]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header & Search Bar */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div>
          <h2 className="text-2xl font-bold text-white font-['Outfit']">Catalog Explorer</h2>
          <p className="text-xs text-slate-400">
            Browse, search, and filter 9,700+ movies processed by the PySpark data pipeline
          </p>
        </div>

        {/* Search & Sort Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <form onSubmit={handleSearchSubmit} className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by title (e.g., Matrix, Shawshank, Inception)..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-slate-950/80 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-amber-500/50 transition-colors"
            />
          </form>

          {/* Sort Selector */}
          <div className="flex items-center space-x-2">
            <SlidersHorizontal className="w-4 h-4 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              className="bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50 cursor-pointer"
            >
              <option value="weighted_score">Bayesian Score</option>
              <option value="avg_rating">Average Rating</option>
              <option value="rating_count">Most Rated</option>
              <option value="year">Release Year</option>
              <option value="title">Title (A-Z)</option>
            </select>

            <button
              onClick={() => setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc')}
              className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-400 hover:text-white transition-colors"
              title="Toggle Sort Order"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Genre Filter Pills */}
        <div className="flex overflow-x-auto pb-1 pt-1 space-x-1.5 scrollbar-thin">
          {GENRES.map((g) => {
            const isSelected = selectedGenre === g;
            return (
              <button
                key={g}
                onClick={() => {
                  setSelectedGenre(g);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all duration-200 ${
                  isSelected
                    ? 'bg-amber-500 text-slate-950 font-semibold shadow-md shadow-amber-500/20'
                    : 'bg-slate-900/80 text-slate-400 border border-slate-800 hover:bg-slate-800 hover:text-white'
                }`}
              >
                {g}
              </button>
            );
          })}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>
          Showing <span className="text-white font-medium">{movies.length}</span> of{' '}
          <span className="text-white font-medium">{total.toLocaleString()}</span> movies
        </span>
        <span>Page {page} of {pages}</span>
      </div>

      {/* Movie Grid */}
      {loading ? (
        <div className="py-32 text-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Loading catalog items...</p>
        </div>
      ) : movies.length === 0 ? (
        <div className="p-16 text-center glass-panel rounded-2xl border border-slate-800 space-y-3">
          <Film className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-base text-slate-300 font-semibold">No movies match your search</p>
          <p className="text-xs text-slate-500">Try clearing genre filters or typing a different title.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {movies.map((m) => (
            <MovieCard
              key={m.movie_id}
              movie={m}
              onSelectMovie={(id) => setSelectedMovieId(id)}
              onExplain={onExplainMovie}
              showRecommendationDetails={false}
            />
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {pages > 1 && (
        <div className="flex items-center justify-center space-x-3 pt-4">
          <button
            disabled={page <= 1}
            onClick={() => setPage(prev => Math.max(1, prev - 1))}
            className="flex items-center space-x-1 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <span className="text-xs text-slate-400 font-mono">
            Page {page} / {pages}
          </span>

          <button
            disabled={page >= pages}
            onClick={() => setPage(prev => Math.min(pages, prev + 1))}
            className="flex items-center space-x-1 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <span>Next</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Movie Details Modal */}
      <MovieDetailModal
        movieId={selectedMovieId}
        onClose={() => setSelectedMovieId(null)}
        onExplain={onExplainMovie}
      />
    </div>
  );
};
