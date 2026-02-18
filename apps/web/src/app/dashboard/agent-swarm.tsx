"use client";

import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface AgentStatus {
  id: string;
  name: string;
  status: "idle" | "running" | "completed" | "failed";
  lastActive: string;
}

interface ExecutionResult {
  roiScore: number;
  recommendation: "BUY" | "SELL" | "HOLD";
  confidence: number;
}

export default function AgentSwarm() {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/agents/status");
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
      }
    } catch (error) {
      console.error("Failed to fetch agent status", error);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRunSwarm = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch("/api/agents/run", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      }
    } catch (error) {
      console.error("Failed to run agent swarm", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full bg-slate-900 border-slate-800 text-slate-100">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-xl font-bold flex items-center gap-2">
          <span>🦞</span> AI Agent Swarm
        </CardTitle>
        <Button
          onClick={handleRunSwarm}
          disabled={loading}
          className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold shadow-lg shadow-cyan-500/20"
        >
          {loading ? (
            <>
              <span className="animate-spin mr-2">⟳</span> Running...
            </>
          ) : (
            "Run Agent Swarm"
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Agent Status Grid */}
        <div>
          <h4 className="text-sm font-medium text-slate-400 mb-3 uppercase tracking-wider">Active Agents</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {agents.length > 0 ? (
              agents.map((agent) => (
                <div key={agent.id} className="p-4 rounded-lg bg-slate-950/50 border border-slate-800 flex justify-between items-center transition-all hover:border-slate-700">
                  <span className="font-medium text-slate-200">{agent.name}</span>
                  <Badge
                    variant="outline"
                    className={
                      agent.status === "running" ? "bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse" :
                      agent.status === "completed" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" :
                      agent.status === "failed" ? "bg-red-500/10 text-red-400 border-red-500/30" :
                      "bg-slate-800 text-slate-400 border-slate-700"
                    }
                  >
                    {agent.status}
                  </Badge>
                </div>
              ))
            ) : (
               <div className="col-span-full text-center text-slate-500 py-8 border border-dashed border-slate-800 rounded-lg">
                 Waiting for agents to report...
               </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        {result && (
          <div className={`mt-6 p-6 rounded-xl border-2 ${
            result.recommendation === "BUY" ? "bg-emerald-950/20 border-emerald-500/30" :
            result.recommendation === "SELL" ? "bg-red-950/20 border-red-500/30" :
            "bg-slate-800/50 border-slate-700"
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-bold text-white flex items-center gap-2">
                Execution Result
              </h4>
              <Badge className={`px-3 py-1 text-sm font-bold ${
                result.recommendation === "BUY" ? "bg-emerald-500 hover:bg-emerald-600" :
                result.recommendation === "SELL" ? "bg-red-500 hover:bg-red-600" :
                "bg-slate-500"
              }`}>
                {result.recommendation}
              </Badge>
            </div>

            <div className="grid grid-cols-2 gap-8">
              <div>
                <span className="text-slate-400 text-sm uppercase tracking-wider">Projected ROI</span>
                <div className={`text-3xl font-mono font-bold mt-1 ${
                  result.roiScore > 0 ? "text-emerald-400" : "text-slate-200"
                }`}>
                  {result.roiScore > 0 ? "+" : ""}{result.roiScore}%
                </div>
              </div>
              <div>
                <span className="text-slate-400 text-sm uppercase tracking-wider">AI Confidence</span>
                <div className="text-3xl font-mono font-bold mt-1 text-cyan-400">
                  {(result.confidence * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
