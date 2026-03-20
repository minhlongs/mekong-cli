import React, { useState, useEffect } from 'react';
import { Lead, LeadStage } from '../types';
import { fetchLeads, deleteLead } from '../api';

interface LeadListProps {
  onSelectLead: (lead: Lead) => void;
  onRefresh: () => void;
}

const stageColors: Record<LeadStage, string> = {
  new: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  contacted: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  qualified: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  proposal: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  negotiation: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  closed_won: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  closed_lost: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
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
  });
};

export const LeadList: React.FC<LeadListProps> = ({ onSelectLead, onRefresh }) => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('all');

  const loadLeads = async () => {
    try {
      const data = await fetchLeads();
      setLeads(data);
    } catch (error) {
      console.error('Failed to load leads:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, []);

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this lead?')) {
      try {
        await deleteLead(id);
        onRefresh();
        loadLeads();
      } catch (error) {
        console.error('Failed to delete lead:', error);
        alert('Failed to delete lead');
      }
    }
  };

  const filteredLeads = leads.filter((lead) => {
    const matchesSearch =
      lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.contact_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.email?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStage = stageFilter === 'all' || lead.stage === stageFilter;
    return matchesSearch && matchesStage;
  });

  if (loading) {
    return <div className="text-center py-8">Loading leads...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 flex-wrap">
        <input
          type="text"
          placeholder="Search leads..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="input flex-1 min-w-[200px]"
        />
        <select
          value={stageFilter}
          onChange={(e) => setStageFilter(e.target.value)}
          className="input w-auto"
        >
          <option value="all">All Stages</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="qualified">Qualified</option>
          <option value="proposal">Proposal</option>
          <option value="negotiation">Negotiation</option>
          <option value="closed_won">Closed Won</option>
          <option value="closed_lost">Closed Lost</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b dark:border-gray-700">
              <th className="p-3 font-semibold">Company</th>
              <th className="p-3 font-semibold">Contact</th>
              <th className="p-3 font-semibold">Stage</th>
              <th className="p-3 font-semibold">Value</th>
              <th className="p-3 font-semibold">Next Follow-up</th>
              <th className="p-3 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredLeads.map((lead) => (
              <tr
                key={lead.id}
                onClick={() => onSelectLead(lead)}
                className="border-b dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
              >
                <td className="p-3 font-medium">{lead.company_name}</td>
                <td className="p-3">
                  <div>{lead.contact_name || '-'}</div>
                  <div className="text-sm text-gray-500">{lead.email || lead.phone || '-'}</div>
                </td>
                <td className="p-3">
                  <span className={`badge ${stageColors[lead.stage]}`}>
                    {lead.stage.replace('_', ' ')}
                  </span>
                </td>
                <td className="p-3">{formatCurrency(lead.estimated_value)}</td>
                <td className="p-3">{formatDate(lead.next_followup_date)}</td>
                <td className="p-3">
                  <button
                    onClick={(e) => handleDelete(e, lead.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredLeads.length === 0 && (
          <div className="text-center py-8 text-gray-500">No leads found</div>
        )}
      </div>
    </div>
  );
};
