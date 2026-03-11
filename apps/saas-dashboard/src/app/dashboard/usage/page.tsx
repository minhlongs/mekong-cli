'use client';

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Zap } from 'lucide-react';
import { StatCard } from '@/components/dashboard/stat-card';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { raasApi, type UsageSummary, type CreditTransaction } from '@/lib/api-client';

const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN ?? 'demo';
const PERIOD_OPTIONS = [7, 14, 30, 90] as const;
type Period = (typeof PERIOD_OPTIONS)[number];

export default function UsagePage() {
  const [period, setPeriod] = useState<Period>(30);
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [history, setHistory] = useState<CreditTransaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void Promise.all([
      raasApi.getUsageSummary(DEMO_TOKEN, period),
      raasApi.getCreditHistory(DEMO_TOKEN, 20),
    ]).then(([sum, hist]) => {
      if (!cancelled) {
        setSummary(sum);
        setHistory(hist.transactions);
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, [period]);

  const maxCredits = summary
    ? Math.max(...(summary.daily_breakdown.map((d) => d.credits_used)), 1)
    : 1;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Usage</h1>
          <p className="text-muted-foreground text-sm mt-1">Credit consumption over time</p>
        </div>
        <div className="flex gap-1">
          {PERIOD_OPTIONS.map((p) => (
            <Button
              key={p}
              size="sm"
              variant={period === p ? 'default' : 'outline'}
              onClick={() => setPeriod(p)}
            >
              {p}d
            </Button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center h-48 items-center">
          <div className="animate-spin h-8 w-8 rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              title="Credits Used"
              value={summary?.total_credits_used ?? 0}
              subtitle={`Last ${period} days`}
              icon={Zap}
            />
            <StatCard
              title="Total Missions"
              value={summary?.total_missions ?? 0}
              subtitle={`${summary?.missions_completed ?? 0} completed`}
              icon={TrendingUp}
              trend="up"
            />
            <StatCard
              title="Avg Per Day"
              value={
                summary && period > 0
                  ? Math.round(summary.total_credits_used / period)
                  : 0
              }
              subtitle="MCU / day"
              icon={BarChart3}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Daily Credit Consumption</CardTitle>
            </CardHeader>
            <CardContent>
              {!summary || summary.daily_breakdown.length === 0 ? (
                <p className="text-sm text-muted-foreground py-6 text-center">
                  No usage data for this period.
                </p>
              ) : (
                <div className="space-y-2">
                  {summary.daily_breakdown.map((day) => (
                    <div key={day.date} className="flex items-center gap-3">
                      <span className="text-xs text-muted-foreground w-24 shrink-0">
                        {day.date}
                      </span>
                      <div className="flex-1 h-5 bg-muted rounded-sm overflow-hidden">
                        <div
                          className="h-full bg-primary rounded-sm transition-all"
                          style={{
                            width: `${Math.round((day.credits_used / maxCredits) * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs font-medium w-16 text-right shrink-0">
                        {day.credits_used} MCU
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Complexity Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                {!summary || Object.keys(summary.complexity_breakdown).length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">No data</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(summary.complexity_breakdown).map(([tier, count]) => (
                      <div key={tier} className="flex items-center justify-between">
                        <span className="text-sm capitalize">{tier}</span>
                        <span className="text-sm font-medium">{count} missions</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">No transactions</p>
                ) : (
                  <div className="space-y-2 divide-y divide-border">
                    {history.map((tx) => (
                      <div key={tx.id} className="flex items-center justify-between py-2">
                        <div>
                          <p className="text-xs font-medium truncate max-w-[160px]">{tx.reason}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(tx.timestamp).toLocaleDateString()}
                          </p>
                        </div>
                        <span
                          className={`text-sm font-semibold ${
                            tx.amount > 0 ? 'text-green-500' : 'text-destructive'
                          }`}
                        >
                          {tx.amount > 0 ? '+' : ''}{tx.amount}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
