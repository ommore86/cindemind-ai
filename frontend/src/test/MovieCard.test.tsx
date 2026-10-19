import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { MovieCard } from '../components/MovieCard';
import { RecommendationItem } from '../types';

describe('MovieCard Component', () => {
  const mockRecMovie: RecommendationItem = {
    movie_id: 1,
    title: 'Toy Story (1995)',
    genres: 'Animation|Children|Comedy',
    year: 1995,
    avg_rating: 4.2,
    rating_count: 150,
    weighted_score: 4.1,
    final_score: 0.88,
    content_score: 0.85,
    collaborative_score: 0.90,
    sentiment_score: 0.95,
    content_available: true,
    collaborative_available: true,
    sentiment_available: true,
    effective_weights: { content: 0.45, collaborative: 0.40, sentiment: 0.15 },
    is_cold_start: false
  };

  it('renders title, genres, and final recommendation score', () => {
    render(<MovieCard movie={mockRecMovie} showRecommendationDetails={true} />);

    expect(screen.getByText('Toy Story (1995)')).toBeInTheDocument();
    expect(screen.getByText('Animation')).toBeInTheDocument();
    expect(screen.getByText('Score: 88%')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument(); // Content
    expect(screen.getByText('90%')).toBeInTheDocument(); // Collaborative
    expect(screen.getByText('95%')).toBeInTheDocument(); // Sentiment
  });

  it('triggers onExplain when "Why this movie?" button is clicked', () => {
    const handleExplain = vi.fn();
    render(
      <MovieCard
        movie={mockRecMovie}
        showRecommendationDetails={true}
        onExplain={handleExplain}
      />
    );

    const button = screen.getByText('Why this movie?');
    fireEvent.click(button);
    expect(handleExplain).toHaveBeenCalledWith(1);
  });
});
