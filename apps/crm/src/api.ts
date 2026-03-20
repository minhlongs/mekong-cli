import type {
  Lead,
  CreateLeadInput,
  UpdateLeadInput,
  Activity,
  CreateActivityInput,
  PipelineSummary
} from './types';

const API_BASE = '/api';

export async function fetchLeads(): Promise<Lead[]> {
  const res = await fetch(`${API_BASE}/leads`);
  if (!res.ok) throw new Error('Failed to fetch leads');
  return res.json();
}

export async function fetchLead(id: string): Promise<Lead> {
  const res = await fetch(`${API_BASE}/leads/${id}`);
  if (!res.ok) throw new Error('Failed to fetch lead');
  return res.json();
}

export async function createLead(input: CreateLeadInput): Promise<Lead> {
  const res = await fetch(`${API_BASE}/leads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error('Failed to create lead');
  return res.json();
}

export async function updateLead(input: UpdateLeadInput): Promise<Lead> {
  const res = await fetch(`${API_BASE}/leads/${input.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error('Failed to update lead');
  return res.json();
}

export async function deleteLead(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/leads/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete lead');
}

export async function fetchActivities(leadId: string): Promise<Activity[]> {
  const res = await fetch(`${API_BASE}/leads/${leadId}/activities`);
  if (!res.ok) throw new Error('Failed to fetch activities');
  return res.json();
}

export async function createActivity(input: CreateActivityInput): Promise<Activity> {
  const res = await fetch(`${API_BASE}/activities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error('Failed to create activity');
  return res.json();
}

export async function fetchPipeline(): Promise<PipelineSummary[]> {
  const res = await fetch(`${API_BASE}/pipeline`);
  if (!res.ok) throw new Error('Failed to fetch pipeline');
  return res.json();
}
