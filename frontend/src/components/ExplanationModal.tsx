import React, { useEffect, useState } from 'react';
import { X, Brain, CheckCircle2, AlertCircle, Sparkles, Film, Star, MessageSquare } from 'lucide-react';
import { ExplanationResponse } from '../types';
import { api } from '../services/api';

interface ExplanationModalProps {
  movieId: number | null;
  userId?: number | null;
  selectedGenre?: string;
  onClose: () => void;
}

export const ExplanationModal: React.FC<ExplanationModalProps> = ({
  movieId,
  userId = 1,
  selectedGenre,
  onClose
}) => {
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!movieId) return;

    setLoading(true);
    setError(null);

    const targetUserId = userId || 1;
    api.getExplanation(targetUserId, movieId, selectedGenre)
      .then((data) => {
        setExplanation(data);
      })
      .catch((err) => {
        setError(err.message || 'Failed to generate explanation.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [movieId, userId, selectedGenre]);

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
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base font-['Outfit']">Explainable AI (XAI) Attribution</h3>
              <p className="text-xs text-slate-400">Model transparency & score evidence breakdown</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="py-24 text-center space-y-3">
            <div className="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm text-slate-400">Synthesizing Explainable AI evidence...</p>
          </div>
        ) : error || !explanation ? (
          <div className="p-8 text-center space-y-4">
            <p className="text-rose-400">{error || 'Explanation not available'}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 text-white text-sm"
            >
              Close
            </button>
          </div>
        ) : (
          <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
            {/* Title & Final Score */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div>
                <span className="text-[10px] text-amber-400 font-mono tracking-wider uppercase block">Target Recommendation</span>
                <h4 className="text-xl font-bold text-white mt-0.5">{explanation.title}</h4>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {explanation.genres.map((g) => (
                    <span key={g} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {g}
                    </span>
                  ))}
                </div>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Final Hybrid Score</span>
                <span className="text-2xl font-extrabold text-amber-400 font-mono">
                  {(explanation.final_score * 100).toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-500 block">Normalized [0.0 - 1.0]</span>
              </div>
            </div>

            {/* Dynamic Natural Language Narrative */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20">
              <div className="flex items-center space-x-2 text-amber-400 text-xs font-semibold mb-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generated Attribution Narrative</span>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed font-sans">
                {explanation.natural_language_explanation}
              </p>
            </div>

            {/* Score Decomposition Bar */}
            <div className="space-y-3">
              <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Dynamic Component Weights & Contributions
              </h5>

              {/* Visual Multi-segment bar */}
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

              {/* Component breakdown tiles */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Content */}
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-cyan-400 font-semibold flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block" />
                      <span>Content-Based</span>
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Weight: {Math.round((explanation.effective_weights.content || 0) * 100)}%
                    </span>
                  </div>
                  <div className="mt-2 text-lg font-bold text-white font-mono">
                    {explanation.scores.content_score != null 
                      ? `${Math.round(explanation.scores.content_score * 100)}%` 
                      : 'N/A'}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    TF-IDF feature cosine similarity on metadata & genres.
                  </p>
                </div>

                {/* Collaborative */}
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-purple-400 font-semibold flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-purple-400 inline-block" />
                      <span>Collaborative</span>
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Weight: {Math.round((explanation.effective_weights.collaborative || 0) * 100)}%
                    </span>
                  </div>
                  <div className="mt-2 text-lg font-bold text-white font-mono">
                    {explanation.scores.collaborative_score != null 
                      ? `${Math.round(explanation.scores.collaborative_score * 100)}%` 
                      : 'Unavailable'}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {explanation.data_coverage.collaborative_available 
                      ? 'Truncated SVD latent interaction patterns.'
                      : 'Cold-start: weight redistributed to active channels.'}
                  </p>
                </div>

                {/* Sentiment */}
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-emerald-400 font-semibold flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
                      <span>Sentiment</span>
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Weight: {Math.round((explanation.effective_weights.sentiment || 0) * 100)}%
                    </span>
                  </div>
                  <div className="mt-2 text-lg font-bold text-white font-mono">
                    {explanation.scores.sentiment_score != null 
                      ? `${Math.round(explanation.scores.sentiment_score * 100)}%` 
                      : 'Unavailable'}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {explanation.data_coverage.sentiment_available
                      ? 'DistilBERT SST-2 sentiment confidence.'
                      : 'No verified reviews; score not penalized.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Matching Evidence: Watched Movies & Genres */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Similar Movies Watched */}
              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2">
                <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Film className="w-3.5 h-3.5 text-amber-400" />
                  <span>Your Similar Highly-Rated Titles</span>
                </h5>
                {explanation.similar_movies_watched.length > 0 ? (
                  <div className="space-y-1.5">
                    {explanation.similar_movies_watched.map((sim) => (
                      <div key={sim.movie_id} className="flex items-center justify-between p-2 rounded bg-slate-900/80 text-xs">
                        <span className="text-slate-200 line-clamp-1 flex-1 font-medium mr-2">{sim.title}</span>
                        <div className="flex items-center space-x-2 text-[10px] whitespace-nowrap">
                          {sim.user_rating && (
                            <span className="text-amber-400 font-semibold">★ {sim.user_rating}</span>
                          )}
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 font-mono">
                            {Math.round(sim.similarity_score * 100)}% match
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    {explanation.data_coverage.is_cold_start
                      ? 'No previous rating history; using genre baseline.'
                      : 'No overlapping titles in immediate watch history.'}
                  </p>
                )}
              </div>

              {/* Review Sentiment Evidence */}
              <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2">
                <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Audience Review Evidence</span>
                </h5>
                {explanation.sentiment_evidence ? (
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Analyzed Reviews:</span>
                      <span className="font-semibold text-white">{explanation.sentiment_evidence.analyzed_reviews}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Positive Feedback:</span>
                      <span className="font-semibold text-emerald-400">
                        {Math.round(explanation.sentiment_evidence.positive_ratio * 100)}%
                      </span>
                    </div>
                    {explanation.sentiment_evidence.sample_quote && (
                      <p className="text-slate-300 italic p-2 rounded bg-slate-900/80 border border-slate-800 text-[11px]">
                        "{explanation.sentiment_evidence.sample_quote}"
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">
                    Sentiment analysis not performed for this title. Missing data honest policy applied.
                  </p>
                )}
              </div>
            </div>

            {/* Coverage & Auditing Flags */}
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-[11px] flex flex-wrap gap-3 items-center justify-between text-slate-400">
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>Cold Start: {explanation.data_coverage.is_cold_start ? 'Active' : 'Personalized'}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                <span>TF-IDF Vectors: Active</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className={`w-3.5 h-3.5 ${explanation.data_coverage.collaborative_available ? 'text-purple-400' : 'text-slate-600'}`} />
                <span>SVD Collab: {explanation.data_coverage.collaborative_available ? 'Available' : 'Excluded'}</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <CheckCircle2 className={`w-3.5 h-3.5 ${explanation.data_coverage.sentiment_available ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span>DistilBERT: {explanation.data_coverage.sentiment_available ? 'Integrated' : 'Excluded'}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
