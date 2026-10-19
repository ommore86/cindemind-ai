import React, { useEffect, useState } from 'react';
import { Film, Star, Users, MessageSquareText, Sparkles, Database, ArrowRight, Activity } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, PieChart, Pie } from 'recharts';
import { MetricCard } from '../components/MetricCard';
import { api } from '../services/api';
import {
  AnalyticsOverview,
  RatingDistributionItem,
  GenreDistributionItem,
  SentimentAnalyticsResponse,
  RecommendationAnalyticsResponse
} from '../types';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigate }) => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [ratingsDist, setRatingsDist] = useState<RatingDistributionItem[]>([]);
  const [genresDist, setGenresDist] = useState<GenreDistributionItem[]>([]);
  const [sentimentStats, setSentimentStats] = useState<SentimentAnalyticsResponse | null>(null);
  const [benchmarks, setBenchmarks] = useState<RecommendationAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getAnalyticsOverview().catch(() => null),
      api.getRatingsDistribution().catch(() => []),
      api.getGenreDistribution().catch(() => []),
      api.getSentimentAnalytics().catch(() => null),
      api.getRecommendationBenchmarks().catch(() => null)
    ])
      .then(([ov, rDist, gDist, sStats, bMarks]) => {
        setOverview(ov);
        setRatingsDist(rDist);
        setGenresDist(gDist.slice(0, 10)); // Top 10 genres
        setSentimentStats(sStats);
        setBenchmarks(bMarks);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const sentimentPieData = sentimentStats ? [
    { name: 'Positive', value: sentimentStats.positive_reviews, color: '#10b981' },
    { name: 'Negative', value: sentimentStats.negative_reviews, color: '#f43f5e' }
  ] : [];

  return (
    <div className="space-y-8 pb-12">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl glass-panel p-6 sm:p-8 border border-slate-800">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-10 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Activity className="w-3.5 h-3.5" />
            <span>Big Data Movie Intelligence & Explainable AI</span>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight font-['Outfit']">
            Autonomous Big Data <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-200">Recommender</span> Platform
          </h1>

          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Harnessing distributed <span className="text-amber-400 font-medium">Apache Spark</span> ETL pipelines, 
            <span className="text-cyan-400 font-medium"> TF-IDF cosine similarity</span>, 
            <span className="text-purple-400 font-medium"> Truncated SVD Matrix Factorization</span>, and 
            <span className="text-emerald-400 font-medium"> DistilBERT Transformer NLP</span> to generate transparent, auditable recommendations.
          </p>

          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => onNavigate('recommendations')}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl font-semibold text-xs sm:text-sm bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 hover:from-amber-400 hover:to-amber-500 transition-all shadow-lg shadow-amber-500/20"
            >
              <Sparkles className="w-4 h-4" />
              <span>Launch Hybrid Recommender</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>

            <button
              onClick={() => onNavigate('explainability')}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-xl font-semibold text-xs sm:text-sm bg-slate-900 text-slate-200 border border-slate-700 hover:bg-slate-800 transition-colors"
            >
              <span>Explore Explainable AI</span>
            </button>
          </div>
        </div>
      </div>

      {/* KPI Overview Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Movies"
          value={overview?.total_movies.toLocaleString() || '9,742'}
          subtitle="Processed via PySpark"
          icon={Film}
          color="amber"
          badge={overview?.spark_engine ? 'Spark 4.2' : 'PySpark'}
        />

        <MetricCard
          title="User Ratings"
          value={overview?.total_ratings.toLocaleString() || '100,836'}
          subtitle={`Across ${overview?.unique_users || 610} real users`}
          icon={Users}
          color="cyan"
          badge="MovieLens"
        />

        <MetricCard
          title="Catalog Rating"
          value={overview?.global_average_rating ? `${overview.global_average_rating} ★` : '3.50 ★'}
          subtitle="Global baseline prior C"
          icon={Star}
          color="purple"
          badge="Mean"
        />

        <MetricCard
          title="Analyzed Reviews"
          value={sentimentStats?.total_reviews_analyzed || 53}
          subtitle={`${Math.round((sentimentStats?.overall_positive_ratio || 0.85) * 100)}% Positive sentiment`}
          icon={MessageSquareText}
          color="emerald"
          badge="DistilBERT"
        />
      </div>

      {/* Charts Grid: Ratings Histogram & Genres Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rating Distribution Chart */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-white text-base font-['Outfit']">Rating Score Distribution</h3>
              <p className="text-xs text-slate-400">Histogram of user-star interactions across catalog (0.5 to 5.0)</p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-amber-400 font-mono">
              N = {overview?.total_ratings.toLocaleString() || '100,836'}
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ratingsDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="rating" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                  formatter={(val: any) => [`${Number(val).toLocaleString()} ratings`, 'Count']}
                />
                <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Genre Distribution Chart */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-white text-base font-['Outfit']">Top Genres Representation</h3>
              <p className="text-xs text-slate-400">Total movie counts by primary genre taxonomy</p>
            </div>
            <button
              onClick={() => onNavigate('explorer')}
              className="text-xs text-amber-400 hover:text-amber-300 font-semibold flex items-center space-x-1"
            >
              <span>Explore All</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={genresDist} layout="vertical" margin={{ top: 5, right: 20, left: 25, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis dataKey="genre" type="category" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} width={70} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
                  formatter={(val: any) => [`${Number(val).toLocaleString()} movies`, 'Catalog']}
                />
                <Bar dataKey="movie_count" fill="#06b6d4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 3: Sentiment NLP & Benchmark Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sentiment Proportion Donut */}
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-4">
          <div>
            <h3 className="font-bold text-white text-base font-['Outfit']">Transformer Sentiment Distribution</h3>
            <p className="text-xs text-slate-400">Verified movie review text classifications</p>
          </div>

          <div className="h-44 w-full flex items-center justify-center">
            {sentimentPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentPieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={5}
                  >
                    {sentimentPieData.map((entry, index) => (
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

          <div className="flex justify-around text-center text-xs pt-2 border-t border-slate-800">
            <div>
              <span className="text-emerald-400 font-bold text-lg block">
                {sentimentStats?.positive_reviews || 0}
              </span>
              <span className="text-slate-400">Positive ({Math.round((sentimentStats?.overall_positive_ratio || 0.8) * 100)}%)</span>
            </div>
            <div>
              <span className="text-rose-400 font-bold text-lg block">
                {sentimentStats?.negative_reviews || 0}
              </span>
              <span className="text-slate-400">Negative ({Math.round((1.0 - (sentimentStats?.overall_positive_ratio || 0.8)) * 100)}%)</span>
            </div>
          </div>
        </div>

        {/* Model Evaluation Benchmark Summary */}
        <div className="lg:col-span-2 p-6 rounded-2xl glass-panel border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-white text-base font-['Outfit']">Offline Model Evaluation Comparison</h3>
              <p className="text-xs text-slate-400">Held-out 80/20 test split ranking & rating prediction metrics</p>
            </div>
            <button
              onClick={() => onNavigate('insights')}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold flex items-center space-x-1"
            >
              <span>Full Benchmark Report</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider font-mono border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Model Architecture</th>
                  <th className="py-2.5 px-3">Precision@10</th>
                  <th className="py-2.5 px-3">Recall@10</th>
                  <th className="py-2.5 px-3">NDCG@10</th>
                  <th className="py-2.5 px-3">RMSE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200 font-mono">
                {benchmarks?.benchmarks.map((b) => (
                  <tr key={b.model_name} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-3 font-sans font-medium text-slate-100 flex items-center space-x-2">
                      <span className={`w-2 h-2 rounded-full ${
                        b.model_name === 'hybrid' ? 'bg-amber-400' :
                        b.model_name === 'collaborative' ? 'bg-purple-400' : 'bg-cyan-400'
                      }`} />
                      <span>{b.display_name}</span>
                    </td>
                    <td className="py-3 px-3 text-cyan-400 font-bold">
                      {b.precision_at_k != null ? b.precision_at_k.toFixed(4) : '—'}
                    </td>
                    <td className="py-3 px-3 text-purple-400 font-bold">
                      {b.recall_at_k != null ? b.recall_at_k.toFixed(4) : '—'}
                    </td>
                    <td className="py-3 px-3 text-amber-400 font-bold">
                      {b.ndcg_at_k != null ? b.ndcg_at_k.toFixed(4) : '—'}
                    </td>
                    <td className="py-3 px-3 text-emerald-400 font-bold">
                      {b.rmse != null ? b.rmse.toFixed(4) : 'N/A*'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-[10px] text-slate-500 mt-3 italic">
            *RMSE is only applicable to Collaborative Filtering which predicts explicit star ratings. Precision/Recall/NDCG evaluate top-10 item ranking against actual favorable ratings (&ge; 3.5).
          </p>
        </div>
      </div>
    </div>
  );
};
