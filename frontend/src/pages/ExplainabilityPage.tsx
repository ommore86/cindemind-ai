import React, { useEffect, useState } from 'react';
import { Brain, Sparkles, CheckCircle2, ShieldCheck, Film, Star, MessageSquare, Layers, ArrowRight } from 'lucide-react';
import { ExplanationResponse, Movie } from '../types';
import { api } from '../services/api';

const FEATURED_MOVIES = [
  { id: 2571, title: 'The Matrix (1999)', genre: 'Sci-Fi|Action' },
  { id: 79132, title: 'Inception (2010)', genre: 'Sci-Fi|Thriller' },
  { id: 318, title: 'The Shawshank Redemption (1994)', genre: 'Drama|Crime' },
  { id: 1, title: 'Toy Story (1995)', genre: 'Animation|Adventure' },
  { id: 58559, title: 'The Dark Knight (2008)', genre: 'Action|Crime' },
  { id: 109487, title: 'Interstellar (2014)', genre: 'Sci-Fi|Drama' }
];

export const ExplainabilityPage: React.FC = () => {
  const [selectedMovieId, setSelectedMovieId] = useState<number>(2571);
  const [selectedUserId, setSelectedUserId] = useState<number>(1);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    api.getExplanation(selectedUserId, selectedMovieId)
      .then((data) => setExplanation(data))
      .catch((err) => setError(err.message || 'Failed to fetch explanation.'))
      .finally(() => setLoading(false));
  }, [selectedMovieId, selectedUserId]);

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <Brain className="w-3.5 h-3.5" />
          <span>Transparent & Verifiable Model Attribution</span>
        </div>

        <h1 className="text-3xl font-extrabold text-white font-['Outfit']">
          Explainable AI (XAI) Attribution Architecture
        </h1>

        <p className="text-slate-300 text-sm max-w-3xl leading-relaxed">
          Traditional recommendation systems operate as uninterpretable black boxes. CineMind AI implements 
          evidence-backed transparent score attribution: every recommendation provides mathematical score 
          decomposition, active weight normalization, feature overlap, and verified audience sentiment quotes.
        </p>

        {/* Core Principles */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-bold text-white">Mathematical Honesty</h4>
              <p className="text-[11px] text-slate-400">Score contributions match backend computations without fabricated values.</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
            <Layers className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-bold text-white">Dynamic Normalization</h4>
              <p className="text-[11px] text-slate-400">Missing components (e.g. unreviewed movies) dynamically redistribute weights.</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-2.5">
            <Sparkles className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <div>
              <h4 className="text-xs font-bold text-white">Fact-Checked Evidence</h4>
              <p className="text-[11px] text-slate-400">Natural language narratives generated directly from user watch logs.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive XAI Sandbox */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
        <div>
          <h3 className="text-lg font-bold text-white font-['Outfit']">Interactive XAI Sandbox</h3>
          <p className="text-xs text-slate-400">Select a target movie and user persona to inspect live attribution evidence</p>
        </div>

        {/* Movie Selector Tabs */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Target Movie
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
            {FEATURED_MOVIES.map((m) => {
              const active = selectedMovieId === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setSelectedMovieId(m.id)}
                  className={`p-2.5 rounded-xl text-left border transition-all ${
                    active
                      ? 'bg-amber-500/10 border-amber-500/40 text-amber-400 shadow-md'
                      : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <span className="text-xs font-bold block line-clamp-1">{m.title}</span>
                  <span className="text-[10px] text-slate-500 block line-clamp-1">{m.genre}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* User Persona Selector */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
            Evaluating Against User Persona
          </label>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 1, label: 'User #1 (Sci-Fi & Action Fan)' },
              { id: 2, label: 'User #2 (Crime & Drama Aficionado)' },
              { id: 3, label: 'User #3 (Animation & Family)' },
              { id: 4, label: 'User #4 (Nolan & Mind-Bending)' },
              { id: 9999, label: 'User #9999 (New Cold-Start User)' }
            ].map((u) => (
              <button
                key={u.id}
                onClick={() => setSelectedUserId(u.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  selectedUserId === u.id
                    ? 'bg-cyan-500 text-slate-950 font-semibold'
                    : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {u.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Live Explanation Panel */}
      {loading ? (
        <div className="py-24 text-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Computing feature overlap and dynamic weights...</p>
        </div>
      ) : error || !explanation ? (
        <div className="p-8 text-center glass-panel rounded-2xl border border-rose-500/30 text-rose-400">
          <p className="font-semibold">{error || 'Could not load explanation for selection.'}</p>
        </div>
      ) : (
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-8">
          {/* Top Title & Score Metric */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800">
            <div>
              <span className="text-xs text-amber-400 font-mono uppercase tracking-wider block">Attribution Evidence</span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white mt-1 font-['Outfit']">{explanation.title}</h2>
              <div className="flex flex-wrap gap-1 mt-2">
                {explanation.genres.map((g) => (
                  <span key={g} className="text-xs px-2.5 py-0.5 rounded bg-slate-800 text-slate-300">
                    {g}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-left sm:text-right">
              <span className="text-[11px] text-slate-400 uppercase tracking-wider block">Final Hybrid Score</span>
              <span className="text-3xl font-black text-amber-400 font-mono">
                {(explanation.final_score * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-slate-500 block">Calculated by Recommendation Engine</span>
            </div>
          </div>

          {/* Dynamic Natural Language Narrative */}
          <div className="p-5 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20">
            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center space-x-1.5 mb-2">
              <Sparkles className="w-4 h-4" />
              <span>Verifiable Natural-Language Explanation</span>
            </h4>
            <p className="text-sm sm:text-base text-slate-200 leading-relaxed">
              {explanation.natural_language_explanation}
            </p>
          </div>

          {/* Detailed Contribution Breakdown */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Mathematical Score Decomposition
            </h4>

            {/* Visual Contribution Bar */}
            <div className="h-4 w-full bg-slate-950 rounded-full overflow-hidden flex border border-slate-800">
              {explanation.effective_weights.content > 0 && (
                <div
                  style={{ width: `${explanation.effective_weights.content * 100}%` }}
                  className="bg-cyan-500 transition-all duration-500"
                  title={`Content: ${(explanation.effective_weights.content * 100).toFixed(1)}%`}
                />
              )}
              {explanation.effective_weights.collaborative > 0 && (
                <div
                  style={{ width: `${explanation.effective_weights.collaborative * 100}%` }}
                  className="bg-purple-500 transition-all duration-500"
                  title={`Collaborative: ${(explanation.effective_weights.collaborative * 100).toFixed(1)}%`}
                />
              )}
              {explanation.effective_weights.sentiment > 0 && (
                <div
                  style={{ width: `${explanation.effective_weights.sentiment * 100}%` }}
                  className="bg-emerald-500 transition-all duration-500"
                  title={`Sentiment: ${(explanation.effective_weights.sentiment * 100).toFixed(1)}%`}
                />
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Content Channel */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-cyan-400 flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                    <span>Content-Based Channel</span>
                  </span>
                  <span className="text-slate-400 font-mono">
                    Weight: {Math.round((explanation.effective_weights.content || 0) * 100)}%
                  </span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {explanation.scores.content_score != null ? `${Math.round(explanation.scores.content_score * 100)}%` : '—'}
                </div>
                <p className="text-xs text-slate-400">
                  Calculated from TF-IDF vector representations of genres, tags, overview, and title keywords.
                </p>
                {explanation.matching_genres.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Matching Genres</span>
                    <div className="flex flex-wrap gap-1">
                      {explanation.matching_genres.map((mg) => (
                        <span key={mg} className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                          {mg}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Collaborative Channel */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-purple-400 flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                    <span>Collaborative Channel</span>
                  </span>
                  <span className="text-slate-400 font-mono">
                    Weight: {Math.round((explanation.effective_weights.collaborative || 0) * 100)}%
                  </span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {explanation.scores.collaborative_score != null ? `${Math.round(explanation.scores.collaborative_score * 100)}%` : 'Unavailable'}
                </div>
                <p className="text-xs text-slate-400">
                  {explanation.data_coverage.collaborative_available
                    ? 'Latent factor interaction predicted via Truncated SVD matrix factorization.'
                    : 'User has no rating matrix history (cold-start); weight dynamically shifted.'}
                </p>
              </div>

              {/* Sentiment Channel */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-emerald-400 flex items-center space-x-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                    <span>Sentiment Channel</span>
                  </span>
                  <span className="text-slate-400 font-mono">
                    Weight: {Math.round((explanation.effective_weights.sentiment || 0) * 100)}%
                  </span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {explanation.scores.sentiment_score != null ? `${Math.round(explanation.scores.sentiment_score * 100)}%` : 'Unavailable'}
                </div>
                <p className="text-xs text-slate-400">
                  {explanation.data_coverage.sentiment_available
                    ? 'DistilBERT SST-2 sentiment confidence aggregated across verified reviews.'
                    : 'No verified reviews exist for this title; missing data penalty avoided.'}
                </p>
              </div>
            </div>
          </div>

          {/* Watched Titles & Verified Reviews Evidence */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            {/* Watched Movies Evidence */}
            <div className="p-5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Film className="w-4 h-4 text-amber-400" />
                <span>Triggering Watched Titles From User Profile</span>
              </h4>
              {explanation.similar_movies_watched.length > 0 ? (
                <div className="space-y-2">
                  {explanation.similar_movies_watched.map((sm) => (
                    <div key={sm.movie_id} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-slate-100 block">{sm.title}</span>
                        {sm.user_rating && (
                          <span className="text-[11px] text-amber-400 font-medium">Your Rating: ★ {sm.user_rating}</span>
                        )}
                      </div>
                      <span className="px-2 py-1 rounded bg-slate-800 text-cyan-400 font-mono font-bold text-xs">
                        {Math.round(sm.similarity_score * 100)}% Similarity
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic p-3 rounded-lg bg-slate-900/40 border border-slate-800">
                  {explanation.data_coverage.is_cold_start
                    ? 'This user is in cold-start mode with zero ratings. Catalog genre priors were applied.'
                    : 'No high-scoring items in user history.'}
                </p>
              )}
            </div>

            {/* Audience Review Sentiment Evidence */}
            <div className="p-5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-emerald-400" />
                <span>Audience Review Text Evidence</span>
              </h4>
              {explanation.sentiment_evidence ? (
                <div className="space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-2 text-center">
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase">Analyzed Reviews</span>
                      <span className="text-base font-bold text-white">{explanation.sentiment_evidence.analyzed_reviews}</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-400 block uppercase">Positive Proportion</span>
                      <span className="text-base font-bold text-emerald-400">
                        {Math.round(explanation.sentiment_evidence.positive_ratio * 100)}%
                      </span>
                    </div>
                  </div>
                  {explanation.sentiment_evidence.sample_quote && (
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Verified Quote</span>
                      <p className="text-slate-200 italic leading-relaxed">
                        "{explanation.sentiment_evidence.sample_quote}"
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic p-3 rounded-lg bg-slate-900/40 border border-slate-800">
                  Audience sentiment text was not available for this movie. The system followed the honest missing-data policy.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
