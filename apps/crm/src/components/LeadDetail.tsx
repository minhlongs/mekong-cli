import React, { useState, useEffect } from 'react';
import { Lead, Activity, ActivityType } from '../types';
import { fetchActivities, createActivity } from '../api';

interface LeadDetailProps {
  lead: Lead;
  onBack: () => void;
  onEdit: () => void;
}

const activityTypes: ActivityType[] = ['call', 'email', 'meeting', 'note', 'task', 'other'];

export const LeadDetail: React.FC<LeadDetailProps> = ({ lead, onBack, onEdit }) => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [newActivity, setNewActivity] = useState({
    activity_type: 'note' as ActivityType,
    description: '',
  });
  const [loading, setLoading] = useState(false);

  const loadActivities = async () => {
    try {
      const data = await fetchActivities(lead.id);
      setActivities(data);
    } catch (error) {
      console.error('Failed to load activities:', error);
    }
  };

  useEffect(() => {
    loadActivities();
  }, [lead.id]);

  const handleAddActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newActivity.description.trim()) return;

    setLoading(true);
    try {
      await createActivity({
        lead_id: lead.id,
        ...newActivity,
      });
      setNewActivity({ activity_type: 'note', description: '' });
      loadActivities();
    } catch (error) {
      console.error('Failed to add activity:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="btn btn-secondary">
          ← Back to List
        </button>
        <button onClick={onEdit} className="btn btn-primary">
          Edit Lead
        </button>
      </div>

      {/* Lead Info */}
      <div className="card">
        <h2 className="text-2xl font-bold mb-4">{lead.company_name}</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Contact Name</p>
            <p>{lead.contact_name || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Email</p>
            <p>{lead.email || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Phone</p>
            <p>{lead.phone || '-'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Stage</p>
            <p className="capitalize">{lead.stage.replace('_', ' ')}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Estimated Value</p>
            <p className="font-semibold">{formatCurrency(lead.estimated_value)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Probability</p>
            <p>{lead.probability}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Last Contact</p>
            <p>{formatDate(lead.last_contact_date)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Next Follow-up</p>
            <p>{formatDate(lead.next_followup_date)}</p>
          </div>
        </div>
        {lead.notes && (
          <div className="mt-4 pt-4 border-t dark:border-gray-700">
            <p className="text-sm text-gray-500 mb-2">Notes</p>
            <p className="whitespace-pre-wrap">{lead.notes}</p>
          </div>
        )}
      </div>

      {/* Activities */}
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Activities</h3>

        {/* Add Activity Form */}
        <form onSubmit={handleAddActivity} className="mb-6 flex gap-2">
          <select
            value={newActivity.activity_type}
            onChange={(e) =>
              setNewActivity({ ...newActivity, activity_type: e.target.value as ActivityType })
            }
            className="input w-auto"
          >
            {activityTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          <input
            type="text"
            value={newActivity.description}
            onChange={(e) =>
              setNewActivity({ ...newActivity, description: e.target.value })
            }
            placeholder="Add a note..."
            className="input flex-1"
          />
          <button type="submit" disabled={loading} className="btn btn-primary">
            Add
          </button>
        </form>

        {/* Activity List */}
        <div className="space-y-3">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium capitalize">{activity.activity_type}</span>
                <span className="text-sm text-gray-500">{formatDate(activity.created_at)}</span>
              </div>
              <p className="text-gray-700 dark:text-gray-300">{activity.description}</p>
            </div>
          ))}
          {activities.length === 0 && (
            <p className="text-gray-500 text-center py-4">No activities yet</p>
          )}
        </div>
      </div>
    </div>
  );
};
