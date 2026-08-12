/**
 * Monitor Agent — log analysis and incident detection
 * Routes to DeepSeek-R1-Distill-32B (worker) for deterministic anomaly reasoning
 */

import type { AgentDefinition } from './types.js';

export const monitorAgent: AgentDefinition = {
  id: 'monitor',
  name: 'Monitor',
  description: 'Analyzes application logs, detects anomalies, and generates incident reports',
  capability: 'observability',
  modelPreference: 'worker',
  systemPrompt:
    'Parse structured and unstructured application logs to identify error patterns, latency spikes, and failure cascades. ' +
    'Correlate errors across services using trace IDs and timestamps to determine root cause. ' +
    'Classify anomalies by severity (P1/P2/P3) and affected service scope before generating an incident report. ' +
    'Include remediation steps and rollback recommendations in every P1 incident report.',
  tools: [
    {
      name: 'log_analyze',
      description: 'Parse and summarize log entries within a given time window',
      parameters: { logStream: { type: 'string' }, startTime: { type: 'string' }, endTime: { type: 'string' } },
    },
    {
      name: 'anomaly_detect',
      description: 'Detect statistical anomalies in metric time series data',
      parameters: { metricName: { type: 'string' }, values: { type: 'array' }, threshold: { type: 'number' } },
    },
    {
      name: 'incident_report',
      description: 'Generate a structured incident report with root cause and remediation steps',
      parameters: { severity: { type: 'string' }, affectedServices: { type: 'array' }, timeline: { type: 'array' } },
    },
  ],
  maxTokens: 4096,
  temperature: 0.1,
};
