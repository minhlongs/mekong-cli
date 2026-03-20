export interface Lead {
  id: string;
  company_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  stage: LeadStage;
  estimated_value: number;
  probability: number;
  last_contact_date?: string;
  next_followup_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export type LeadStage =
  | 'new'
  | 'contacted'
  | 'qualified'
  | 'proposal'
  | 'negotiation'
  | 'closed_won'
  | 'closed_lost';

export interface Activity {
  id: string;
  lead_id: string;
  activity_type: ActivityType;
  description: string;
  created_at: string;
}

export type ActivityType = 'call' | 'email' | 'meeting' | 'note' | 'task' | 'other';

export interface PipelineSummary {
  stage: string;
  count: number;
  total_value: number;
  weighted_value: number;
}

export interface CreateLeadInput {
  company_name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  stage?: LeadStage;
  estimated_value?: number;
  probability?: number;
  notes?: string;
}

export interface UpdateLeadInput extends Partial<CreateLeadInput> {
  id: string;
}

export interface CreateActivityInput {
  lead_id: string;
  activity_type: ActivityType;
  description: string;
}
