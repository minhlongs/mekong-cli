import React, { useState, useEffect } from 'react';
import { PipelineSummary, Lead } from '../types';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalLeads: 0,
    totalValue: 0,
    weightedValue: 0,
    newThisMonth: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [pipelineRes, leadsRes] = await Promise.all([
          fetch('/api/pipeline'),
          fetch('/api/leads'),
        ]);
        const pipeline: PipelineSummary[] = await pipelineRes.json();
        const leads: Lead[] = await leadsRes.json();

        const totalValue = pipeline.reduce((sum, p) => sum + p.total_value, 0);
        const weightedValue = pipeline.reduce((sum, p) => sum + p.weighted_value, 0);
        const now = new Date();
        const monthAgo = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
        const newThisMonth = leads.filter((l) => new Date(l.created_at) > monthAgo).length;

        setStats({
          totalLeads: leads.length,
          totalValue,
          weightedValue,
          newThisMonth,
        });
      } catch (error) {
        console.error('Failed to load stats:', error);
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const statCards = [
    { label: 'Total Leads', value: stats.totalLeads, color: 'text-blue-600' },
    { label: 'Pipeline Value', value: formatCurrency(stats.totalValue), color: 'text-green-600' },
    { label: 'Weighted Value', value: formatCurrency(stats.weightedValue), color: 'text-purple-600' },
    { label: 'New This Month', value: stats.newThisMonth, color: 'text-orange-600' },
  ];

  if (loading) {
    return <div className="text-center py-8">Loading dashboard...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {statCards.map((stat) => (
        <div key={stat.label} className="card">
          <p className="text-sm text-gray-500 mb-1">{stat.label}</p>
          <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
        </div>
      ))}
    </div>
  );
};
