import React, { useState } from 'react';
import { Lead, LeadStage, CreateLeadInput } from '../types';
import { createLead, updateLead } from '../api';

interface LeadFormProps {
  lead?: Lead | null;
  onSuccess: () => void;
  onCancel: () => void;
}

const stages: LeadStage[] = [
  'new',
  'contacted',
  'qualified',
  'proposal',
  'negotiation',
  'closed_won',
  'closed_lost',
];

export const LeadForm: React.FC<LeadFormProps> = ({ lead, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState<CreateLeadInput>({
    company_name: lead?.company_name || '',
    contact_name: lead?.contact_name || '',
    email: lead?.email || '',
    phone: lead?.phone || '',
    stage: lead?.stage || 'new',
    estimated_value: lead?.estimated_value || 0,
    probability: lead?.probability || 0,
    notes: lead?.notes || '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);

    try {
      if (lead) {
        await updateLead({ ...formData, id: lead.id });
      } else {
        await createLead(formData);
      }
      onSuccess();
    } catch (err) {
      setError('Failed to save lead. Please try again.');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-bold mb-4">{lead ? 'Edit Lead' : 'New Lead'}</h2>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Company Name *</label>
          <input
            type="text"
            value={formData.company_name}
            onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
            className="input"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Contact Name</label>
          <input
            type="text"
            value={formData.contact_name}
            onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
            className="input"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="input"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Phone</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="input"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Stage</label>
          <select
            value={formData.stage}
            onChange={(e) => setFormData({ ...formData, stage: e.target.value as LeadStage })}
            className="input"
          >
            {stages.map((stage) => (
              <option key={stage} value={stage}>
                {stage.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Estimated Value ($)</label>
          <input
            type="number"
            value={formData.estimated_value}
            onChange={(e) =>
              setFormData({ ...formData, estimated_value: parseInt(e.target.value) || 0 })
            }
            className="input"
            min="0"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Probability (%)</label>
          <input
            type="number"
            value={formData.probability}
            onChange={(e) =>
              setFormData({ ...formData, probability: parseInt(e.target.value) || 0 })
            }
            className="input"
            min="0"
            max="100"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Notes</label>
        <textarea
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          className="input"
          rows={4}
        />
      </div>

      <div className="flex gap-4 justify-end pt-4">
        <button type="button" onClick={onCancel} className="btn btn-secondary">
          Cancel
        </button>
        <button type="submit" disabled={saving} className="btn btn-primary">
          {saving ? 'Saving...' : lead ? 'Update Lead' : 'Create Lead'}
        </button>
      </div>
    </form>
  );
};
