import React, { useState, useEffect } from 'react';
import { PipelineSummary } from '../types';
import { fetchPipeline } from '../api';

interface PipelineBoardProps {
  onStageClick: (stage: string) => void;
}

const stageColors: Record<string, string> = {
  new: 'border-t-blue-500',
  contacted: 'border-t-yellow-500',
  qualified: 'border-t-purple-500',
  proposal: 'border-t-orange-500',
  negotiation: 'border-t-pink-500',
  closed_won: 'border-t-green-500',
  closed_lost: 'border-t-red-500',
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
};

export const PipelineBoard: React.FC<PipelineBoardProps> = ({ onStageClick }) => {
  const [pipeline, setPipeline] = useState<PipelineSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPipeline = async () => {
      try {
        const data = await fetchPipeline();
        setPipeline(data);
      } catch (error) {
        console.error('Failed to load pipeline:', error);
      } finally {
        setLoading(false);
      }
    };
    loadPipeline();
  }, []);

  if (loading) {
    return <div className="text-center py-8">Loading pipeline...</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {pipeline.map((item) => (
        <div
          key={item.stage}
          onClick={() => onStageClick(item.stage)}
          className={`card border-t-4 ${stageColors[item.stage]} cursor-pointer hover:shadow-lg transition-shadow`}
        >
          <h3 className="font-bold capitalize text-lg mb-2">
            {item.stage.replace('_', ' ')}
          </h3>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Deals:</span>
              <span className="font-medium">{item.count}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Total Value:</span>
              <span className="font-medium">{formatCurrency(item.total_value)}</span>
            </div>
            <div className="flex justify-between pt-2 border-t dark:border-gray-700">
              <span className="text-gray-500">Weighted:</span>
              <span className="font-semibold text-green-600 dark:text-green-400">
                {formatCurrency(item.weighted_value)}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
