'use client';

import { useState } from 'react';
import { Key, Webhook, Users, Copy, Eye, EyeOff, Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const TIERS = [
  { name: 'Starter', price: '$49/mo', credits: 200, current: true },
  { name: 'Pro', price: '$149/mo', credits: 1000, current: false },
  { name: 'Enterprise', price: '$499/mo', credits: 'Unlimited', current: false },
];

export default function SettingsPage() {
  const [apiKeyVisible, setApiKeyVisible] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookSaved, setWebhookSaved] = useState(false);
  const [copied, setCopied] = useState(false);

  const maskedKey = 'mk_live_••••••••••••••••••••••••••••••••';
  const displayKey = apiKeyVisible ? 'mk_live_demo_key_replace_with_real_value' : maskedKey;

  function handleCopy() {
    void navigator.clipboard.writeText('mk_live_demo_key_replace_with_real_value');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleSaveWebhook(e: React.FormEvent) {
    e.preventDefault();
    setWebhookSaved(true);
    setTimeout(() => setWebhookSaved(false), 3000);
  }

  return (
    <div className="space-y-8 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">
          API keys, webhooks, and subscription management
        </p>
      </div>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Keys
          </CardTitle>
          <CardDescription>Use your API key to authenticate requests.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Live API Key</Label>
            <div className="flex gap-2">
              <Input
                readOnly
                value={displayKey}
                className="font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => setApiKeyVisible((v) => !v)}
                aria-label="Toggle visibility"
              >
                {apiKeyVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopy}
                aria-label="Copy key"
              >
                {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Keep this secret. Never expose in client-side code.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Webhooks */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Webhook className="h-4 w-4" />
            Webhook Configuration
          </CardTitle>
          <CardDescription>
            Receive real-time events: mission.created, mission.completed, credits.depleted.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveWebhook} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="webhook-url">Webhook URL</Label>
              <Input
                id="webhook-url"
                type="url"
                placeholder="https://your-app.com/webhooks/raas"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" disabled={!webhookUrl}>
                Save Webhook
              </Button>
              {webhookSaved && (
                <span className="text-sm text-green-500 flex items-center gap-1">
                  <Check className="h-3 w-3" /> Saved
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Events are signed with HMAC-SHA256. Verify the{' '}
              <code className="font-mono">X-RaaS-Signature</code> header.
            </p>
          </form>
        </CardContent>
      </Card>

      {/* Team */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-4 w-4" />
            Team
          </CardTitle>
          <CardDescription>Manage team members and permissions.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Team management is available on Pro and Enterprise plans.
          </p>
          <Button variant="outline" className="mt-3" asChild>
            <a href="https://polar.sh/mekong" target="_blank" rel="noreferrer">
              Upgrade Plan
            </a>
          </Button>
        </CardContent>
      </Card>

      {/* Subscription */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Subscription</CardTitle>
          <CardDescription>Current plan and upgrade options.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {TIERS.map((tier) => (
              <div
                key={tier.name}
                className={`rounded-lg border p-4 space-y-1 ${
                  tier.current
                    ? 'border-primary bg-primary/5'
                    : 'border-border'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm">{tier.name}</span>
                  {tier.current && (
                    <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                      Current
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{tier.price}</p>
                <p className="text-xs font-medium">{tier.credits} credits/mo</p>
                {!tier.current && (
                  <Button size="sm" variant="outline" className="w-full mt-2" asChild>
                    <a href="https://polar.sh/mekong" target="_blank" rel="noreferrer">
                      Upgrade
                    </a>
                  </Button>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
