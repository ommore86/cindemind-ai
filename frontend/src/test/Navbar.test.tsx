import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Navbar } from '../components/Navbar';
import { MetricCard } from '../components/MetricCard';
import { Star } from 'lucide-react';

describe('Navbar Component', () => {
  it('renders branding and triggers tab change on click', () => {
    const setActiveTab = vi.fn();
    render(<Navbar activeTab="dashboard" setActiveTab={setActiveTab} backendHealthy={true} />);

    expect(screen.getByText('CineMind')).toBeInTheDocument();
    expect(screen.getByText('AI')).toBeInTheDocument();

    const explorerButton = screen.getAllByText('Movie Explorer')[0];
    fireEvent.click(explorerButton);
    expect(setActiveTab).toHaveBeenCalledWith('explorer');
  });

  it('displays online backend badge when backendHealthy is true', () => {
    render(<Navbar activeTab="dashboard" setActiveTab={vi.fn()} backendHealthy={true} />);
    expect(screen.getByText('PySpark & API Connected')).toBeInTheDocument();
  });
});

describe('MetricCard Component', () => {
  it('renders title, value, and subtitle correctly', () => {
    render(
      <MetricCard
        title="Total Movies"
        value="9,742"
        subtitle="Catalog verified"
        icon={Star}
        color="amber"
      />
    );

    expect(screen.getByText('Total Movies')).toBeInTheDocument();
    expect(screen.getByText('9,742')).toBeInTheDocument();
    expect(screen.getByText('Catalog verified')).toBeInTheDocument();
  });
});
