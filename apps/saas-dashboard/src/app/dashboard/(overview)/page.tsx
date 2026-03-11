'use client';

import { useEffect, useState } from 'react';
import { StatCard } from '@/components/analytics/stat-card';
import { RevenueChart } from '@/components/charts/revenue-chart';
import { MetricsChart } from '@/components/charts/metrics-chart';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

const mockRevenueData = [
  { date: 'Mon', value: 4000 },
  { date: 'Tue', value: 3000 },
  { date: 'Wed', value: 5000 },
  { date: 'Thu', value: 4500 },
  { date: 'Fri', value: 6000 },
  { date: 'Sat', value: 5500 },
  { date: 'Sun', value: 7000 },
];

const mockMetricsData = [
  { name: 'Mon', users: 100, revenue: 400 },
  { name: 'Tue', users: 150, revenue: 300 },
  { name: 'Wed', users: 200, revenue: 550 },
  { name: 'Thu', users: 180, revenue: 480 },
  { name: 'Fri', users: 250, revenue: 620 },
  { name: 'Sat', users: 220, revenue: 580 },
  { name: 'Sun', users: 300, revenue: 750 },
];

export default function DashboardOverview() {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  if (!isLoaded) {
    return <div className="p-6">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard Overview
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Welcome to your SaaS dashboard
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm text-gray-500 dark:text-gray-400">Current Plan</p>
            <Badge variant="secondary" className="text-sm">
              Free Plan
            </Badge>
          </div>
          <Button asChild size="sm">
            <Link href="/dashboard/subscription">Upgrade</Link>
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Revenue"
          value="$35,000"
          change="12.5%"
          changeType="positive"
        />
        <StatCard
          title="Active Users"
          value="1,234"
          change="8.2%"
          changeType="positive"
        />
        <StatCard
          title="MRR"
          value="$12,500"
          change="3.1%"
          changeType="positive"
        />
        <StatCard
          title="Churn Rate"
          value="2.4%"
          change="0.5%"
          changeType="negative"
        />
      </div>

      {/* Revenue Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Revenue Trend
        </h2>
        <RevenueChart data={mockRevenueData} />
      </div>

      {/* Metrics Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Users & Revenue
        </h2>
        <MetricsChart data={mockMetricsData} />
      </div>
    </div>
  );
}
