import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { ExplorerPage } from './pages/ExplorerPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { ExplainabilityPage } from './pages/ExplainabilityPage';
import { SentimentPage } from './pages/SentimentPage';
import { InsightsPage } from './pages/InsightsPage';
import { api } from './services/api';
import { Film, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);
  const [explainMovieId, setExplainMovieId] = useState<number | null>(null);

  useEffect(() => {
    // Check backend health dynamically using configured base URL
    api.checkHealth()
      .then(setBackendHealthy)
      .catch(() => setBackendHealthy(false));
  }, []);

  const handleExplainMovie = (movieId: number) => {
    setExplainMovieId(movieId);
    setActiveTab('recommendations');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-amber-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendHealthy={backendHealthy}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {activeTab === 'dashboard' && (
          <DashboardPage onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'explorer' && (
          <ExplorerPage onExplainMovie={handleExplainMovie} />
        )}
        {activeTab === 'recommendations' && (
          <RecommendationsPage initialMovieIdToExplain={explainMovieId} />
        )}
        {activeTab === 'explainability' && (
          <ExplainabilityPage />
        )}
        {activeTab === 'sentiment' && (
          <SentimentPage />
        )}
        {activeTab === 'insights' && (
          <InsightsPage />
        )}
      </main>

      {/* Cinematic Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-8 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded-md bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <Film className="w-3.5 h-3.5" />
            </div>
            <span className="font-semibold text-slate-300 font-['Outfit']">CineMind AI</span>
            <span>&copy; {new Date().getFullYear()}</span>
            <span>• Final-Year AI & Data Science Engineering Project</span>
          </div>

          <div className="flex items-center space-x-6 text-slate-400">
            <span>Apache Spark 4.2</span>
            <span>PyTorch</span>
            <span>Hugging Face Transformers</span>
            <span>FastAPI</span>
            <span>React + Vite</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
