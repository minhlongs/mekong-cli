'use client';

import { useEffect, useState } from 'react';
import { Plus, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { MissionStatusBadge } from '@/components/dashboard/mission-status-badge';
import {
  raasApi,
  type Mission,
  type MissionComplexity,
} from '@/lib/api-client';

const DEMO_TOKEN = process.env.NEXT_PUBLIC_DEMO_TOKEN ?? 'demo';

const COMPLEXITY_OPTIONS: { value: MissionComplexity; label: string; cost: string }[] = [
  { value: 'simple', label: 'Simple', cost: '1 MCU' },
  { value: 'standard', label: 'Standard', cost: '3 MCU' },
  { value: 'complex', label: 'Complex', cost: '5 MCU' },
];

export default function MissionsPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [goal, setGoal] = useState('');
  const [complexity, setComplexity] = useState<MissionComplexity>('simple');
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function loadMissions() {
    setLoading(true);
    try {
      const data = await raasApi.listMissions(DEMO_TOKEN, 50, 0);
      setMissions(data);
    } catch {
      // silent — show empty state
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadMissions(); }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!goal.trim()) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const mission = await raasApi.submitMission(DEMO_TOKEN, goal.trim(), complexity);
      setMissions((prev) => [mission, ...prev]);
      setGoal('');
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Missions</h1>
          <p className="text-muted-foreground text-sm mt-1">Submit and track AI missions</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void loadMissions()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Submit New Mission
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="goal">Goal</Label>
              <Input
                id="goal"
                placeholder="Describe your mission objective..."
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                disabled={submitting}
                minLength={3}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Complexity</Label>
              <div className="flex gap-2">
                {COMPLEXITY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setComplexity(opt.value)}
                    className={`flex-1 px-3 py-2 rounded-md border text-sm font-medium transition-colors ${
                      complexity === opt.value
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border hover:bg-accent text-muted-foreground'
                    }`}
                  >
                    <div>{opt.label}</div>
                    <div className="text-xs opacity-70">{opt.cost}</div>
                  </button>
                ))}
              </div>
            </div>
            {submitError && (
              <p className="text-sm text-destructive">{submitError}</p>
            )}
            <Button type="submit" disabled={submitting || !goal.trim()}>
              {submitting ? 'Submitting…' : 'Submit Mission'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Mission History</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin h-6 w-6 rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : missions.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">
              No missions yet. Submit one above to get started.
            </p>
          ) : (
            <div className="space-y-0 divide-y divide-border">
              {missions.map((m) => (
                <div key={m.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{m.goal}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {m.complexity} &middot; {m.credits_cost} MCU &middot;{' '}
                      {new Date(m.created_at).toLocaleString()}
                    </p>
                    {m.error_message && (
                      <p className="text-xs text-destructive mt-1">{m.error_message}</p>
                    )}
                  </div>
                  <MissionStatusBadge status={m.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
