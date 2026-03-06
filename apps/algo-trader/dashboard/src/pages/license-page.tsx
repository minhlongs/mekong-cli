/**
 * License Management page: license list, audit logs, and analytics tabs.
 * Provides UI for managing RaaS licenses, viewing usage analytics, and audit trails.
 */
import { useState } from 'react';
import { useLicenses } from '../hooks/use-licenses';
import { LicenseListTable } from '../components/license-list-table';
import { CreateLicenseModal } from '../components/create-license-modal';
import { AuditLogViewer } from '../components/audit-log-viewer';
import { UsageAnalyticsDashboard } from '../components/usage-analytics-dashboard';

type TabType = 'licenses' | 'audit-logs' | 'analytics';

const TABS: { id: TabType; label: string }[] = [
  { id: 'licenses', label: 'Licenses' },
  { id: 'audit-logs', label: 'Audit Logs' },
  { id: 'analytics', label: 'Analytics' },
];

function Card({ children }: { children: React.ReactNode }) {
  return (
    <section className="bg-bg-card border border-bg-border rounded-lg p-6">
      {children}
    </section>
  );
}

export function LicensePage() {
  const [activeTab, setActiveTab] = useState<TabType>('licenses');
  const { licenses, loading, error, revokeLicense, deleteLicense, reload } = useLicenses();
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedLicenseId, setSelectedLicenseId] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  function handleCreateLicense() {
    setModalOpen(true);
  }

  function handleSuccess(generatedKey: string) {
    setSuccessMessage(`License key generated: ${generatedKey.slice(0, 16)}...`);
    setModalOpen(false);
    setTimeout(() => setSuccessMessage(null), 5000);
    reload();
  }

  async function handleRevoke(licenseId: string) {
    await revokeLicense(licenseId);
    reload();
  }

  async function handleDelete(licenseId: string) {
    await deleteLicense(licenseId);
    reload();
  }

  function handleViewAudit(licenseId: string) {
    setSelectedLicenseId(licenseId);
    setActiveTab('audit-logs');
  }

  function renderLicensesTab() {
    return (
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white text-sm font-semibold">License Keys</h3>
          <button
            onClick={handleCreateLicense}
            className="px-4 py-2 bg-accent text-bg-primary text-sm font-semibold rounded hover:bg-accent/90 transition-colors"
          >
            Create License
          </button>
        </div>

        {/* Success Toast */}
        {successMessage && (
          <div className="mb-4 p-3 bg-profit/10 border border-profit/40 rounded text-profit text-sm flex items-center justify-between">
            <span>{successMessage}</span>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-profit/70 hover:text-profit ml-4"
            >
              <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-loss/10 border border-loss/40 rounded text-loss text-sm">
            Error: {error}
          </div>
        )}

        <LicenseListTable
          licenses={licenses}
          loading={loading}
          onRevoke={handleRevoke}
          onDelete={handleDelete}
          onViewAudit={handleViewAudit}
        />
      </Card>
    );
  }

  function renderAuditLogsTab() {
    return (
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white text-sm font-semibold">Audit Logs</h3>
          {selectedLicenseId && (
            <button
              onClick={() => setSelectedLicenseId(null)}
              className="text-xs text-muted hover:text-white underline"
            >
              View all licenses
            </button>
          )}
        </div>
        <AuditLogViewer licenseId={selectedLicenseId || undefined} />
      </Card>
    );
  }

  function renderAnalyticsTab() {
    return (
      <Card>
        <UsageAnalyticsDashboard />
      </Card>
    );
  }

  return (
    <div className="space-y-6 font-mono">
      {/* Page header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-white text-lg font-bold tracking-tight">License Management</h2>
          <p className="text-muted text-xs mt-0.5">Manage RaaS licenses and view usage analytics</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-bg-border">
        <nav className="flex gap-4">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-1 py-2 text-sm font-mono border-b-2 transition-colors
                ${
                  activeTab === tab.id
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:text-white'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'licenses' && renderLicensesTab()}
      {activeTab === 'audit-logs' && renderAuditLogsTab()}
      {activeTab === 'analytics' && renderAnalyticsTab()}

      {/* Create License Modal */}
      <CreateLicenseModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSuccess={handleSuccess}
      />
    </div>
  );
}

export default LicensePage;
