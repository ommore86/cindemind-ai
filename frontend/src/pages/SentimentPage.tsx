import React, { useEffect, useState } from 'react';
import { MessageSquareText, ThumbsUp, ThumbsDown, Sparkles, Send, AlertCircle, Info, Star } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { SentimentAnalyticsResponse, SentimentAnalysisResponse } from '../types';
import { api } from '../services/api';

const SAMPLE_REVIEWS = [
  "A breathtaking visual triumph with brilliant acting and emotional depth.",
  "An absolute waste of time with predictable tropes and clunky dialogue.",
  "A solid and charming adventure that falters slightly in the final act.",
  "Christopher Nolan delivers another mind-bending masterclass in suspense and practical effects."
];

export const SentimentPage: React.FC = () => {
  const [stats, setStats] = useState<SentimentAnalyticsResponse | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  // Live inference state
  const [inputText, setInputText] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [inferenceResult, setInferenceResult] = useState<SentimentAnalysisResponse | null>(null);
  const [inferenceError, setInferenceError] = useState<string | null>(null);

  useEffect(() => {
    setLoadingStats(true);
    api.getSentimentAnalytics()
      .then((data) => setStats(data))
      .catch((err) => console.error('Failed to load sentiment stats:', err))
      .finally(() => setLoadingStats(false));
  }, []);

  const handleAnalyze = async (textToAnalyze?: string) => {
    const text = textToAnalyze || inputText;
    if (!text.trim()) return;

    setAnalyzing(true);
    setInferenceError(null);

    try {
      const res = await api.analyzeSentiment(text);
      setInferenceResult(res);
    } catch (err: any) {
      setInferenceError(err.message || 'Sentiment analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  const pieData = stats ? [
    { name: 'Positive', value: stats.positive_reviews, color: '#10b981' },
    { name: 'Negative', value: stats.negative_reviews, color: '#f43f5e' }
  ] : [];

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <MessageSquareText className="w-3.5 h-3.5" />
          <span>Transformer NLP Sentiment Intelligence</span>
        </div>

        <h1 className="text-3xl font-extrabold text-white font-['Outfit']">
          Movie Review Sentiment Analysis
        </h1>

        <p className="text-slate-300 text-sm max-w-3xl leading-relaxed">
          Powered by Hugging Face’s <span className="text-emerald-400 font-medium">distilbert-base-uncased-finetuned-sst-2-english</span>,
          CineMind AI processes authentic audience and critic review text to extract sentiment polarity and confidence scores.
        </p>

        <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-start space-x-2.5 text-xs text-slate-400">
          <Info className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
          <span>
            <strong>Academic Note:</strong> Sentiment describes verified sample review text and does not claim to represent all audience opinions.
            Movies with zero reviews have explicitly unavailable sentiment rather than fabricated neutral scores.
          </span>
        </div>
      </div>

      {/* Live Interactive Transformer Inference Playground */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white font-['Outfit'] flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <span>Real-Time DistilBERT Inference Playground</span>
            </h3>
            <p className="text-xs text-slate-400">
              Type or paste any movie review to classify sentiment live with CPU/GPU batched inference
            </p>
          </div>

          <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-400 hidden sm:inline">
            Model: DistilBERT SST-2
          </span>
        </div>

        <div className="space-y-3">
          <textarea
            rows={3}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your review (e.g. 'The visuals and score were extraordinary, but the plot dragged in the middle...')"
            className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50 transition-colors resize-none"
          />

          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Presets */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
              <span>Try preset:</span>
              {SAMPLE_REVIEWS.map((sample, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInputText(sample);
                    handleAnalyze(sample);
                  }}
                  className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors text-[11px]"
                >
                  Preset {idx + 1}
                </button>
              ))}
            </div>

            <button
              onClick={() => handleAnalyze()}
              disabled={analyzing || !inputText.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 text-slate-950 hover:bg-emerald-400 disabled:opacity-50 transition-colors shadow-md shadow-emerald-500/20"
            >
              <Send className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
              <span>{analyzing ? 'Analyzing with Transformer...' : 'Run Sentiment Inference'}</span>
            </button>
          </div>
        </div>

        {/* Inference Outcome */}
        {inferenceResult && (
          <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Predicted Label</span>
              <div className="flex items-center space-x-2 mt-1">
                {inferenceResult.label === 'POSITIVE' ? (
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1.5">
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>POSITIVE POLARITY</span>
                  </span>
                ) : (
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center space-x-1.5">
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>NEGATIVE POLARITY</span>
                  </span>
                )}
              </div>
            </div>

            <div className="text-left sm:text-right">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Softmax Confidence</span>
              <span className="text-2xl font-black text-white font-mono">
                {(inferenceResult.confidence * 100).toFixed(2)}%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Dataset Sentiment Overview & Top Titles */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Donut Chart */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-4">
          <div>
            <h3 className="font-bold text-white text-base font-['Outfit']">Overall Review Distribution</h3>
            <p className="text-xs text-slate-400">Total verified corpus reviews analyzed</p>
          </div>

          <div className="h-52 w-full flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={75}
                    paddingAngle={4}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-xs text-slate-500">Loading sentiment distribution...</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 text-center pt-2 border-t border-slate-800">
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-emerald-400 font-bold text-lg block">{stats?.positive_reviews || 0}</span>
              <span className="text-[11px] text-slate-400">Positive ({Math.round((stats?.overall_positive_ratio || 0.8) * 100)}%)</span>
            </div>
            <div className="p-2 rounded bg-slate-950 border border-slate-800">
              <span className="text-rose-400 font-bold text-lg block">{stats?.negative_reviews || 0}</span>
              <span className="text-[11px] text-slate-400">Negative ({Math.round((1 - (stats?.overall_positive_ratio || 0.8)) * 100)}%)</span>
            </div>
          </div>
        </div>

        {/* Highest Positively Reviewed Movies */}
        <div className="lg:col-span-2 p-6 rounded-2xl glass-panel border border-slate-800 space-y-4">
          <div>
            <h3 className="font-bold text-white text-base font-['Outfit']">Top Positively Reviewed Titles</h3>
            <p className="text-xs text-slate-400">Aggregated sentiment scores &ge; 2 verified reviews</p>
          </div>

          <div className="space-y-2.5">
            {stats?.top_sentiment_movies.map((m, idx) => (
              <div key={m.movie_id} className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="w-6 h-6 rounded-full bg-slate-900 text-slate-400 flex items-center justify-center font-mono text-xs font-bold">
                    {idx + 1}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-white">{m.title}</h4>
                    <span className="text-[11px] text-slate-500">{m.reviews_count} verified reviews</span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-xs font-bold text-emerald-400 font-mono">
                    {Math.round(m.sentiment_score * 100)}% Positive
                  </span>
                  <div className="w-24 h-1.5 bg-slate-800 rounded-full overflow-hidden mt-1">
                    <div
                      style={{ width: `${m.sentiment_score * 100}%` }}
                      className="h-full bg-emerald-500 rounded-full"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
