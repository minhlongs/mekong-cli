'use client';

import { useEffect, useState } from 'react';
import { CreditCard, Rocket, CheckCircle, XCircle } from 'lucide-react';
import { StatCard } from '@/components/dashboard/stat-card';
import { MissionStatusBadge } from '@/components/dashboard/mission-status-badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { raasApi, type ActivityItem, type CreditBalance, type UsageSummary } from '@/lib/api-client';

const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN ?? 'demo';

export default function DashboardPage() {
  const [balance, setBalance] = useState<CreditBalance | null>(null);
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [bal, sum, act] = await Promise.all([
          raasApi.getBalance(DEMO_TOKEN),
          raasApi.getUsageSummary(DEMO_TOKEN, 30),
          raasApi.getActivity(DEMO_TOKEN, 5),
        ]);
        if (!cancelled) {
          setBalance(bal);
          setSummary(sum);
          setActivity(act.activity);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive">
        {error}
      </div>
    );
  }

  const successRate = summary && summary.total_missions > 0
    ? Math.round((summary.missions_completed / summary.total_missions) * 100)
    : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Overview</h1>
        <p className="text-muted-foreground text-sm mt-1">Last 30 days</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Credit Balance"
          value={balance?.balance ?? 0}
          subtitle="MCU available"
          icon={CreditCard}
        />
        <StatCard
          title="Total Missions"
          value={summary?.total_missions ?? 0}
          subtitle={`${summary?.total_credits_used ?? 0} credits used`}
          icon={Rocket}
        />
        <StatCard
          title="Completed"
          value={summary?.missions_completed ?? 0}
          subtitle={`${successRate}% success rate`}
          icon={CheckCircle}
          trend="up"
        />
        <StatCard
          title="Failed"
          value={summary?.missions_failed ?? 0}
          subtitle="missions failed"
          icon={XCircle}
          trend={summary?.missions_failed ? 'down' : 'neutral'}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {activity.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No missions yet. Submit your first mission to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {activity.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between py-2 border-b border-border last:border-0"
                >
                  <div className="min-w-0 flex-1 mr-4">
                    <p className="text-sm font-medium truncate">{item.goal}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {new Date(item.created_at).toLocaleDateString()} &middot; {item.credits_cost} MCU
                    </p>
                  </div>
                  <MissionStatusBadge status={item.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
