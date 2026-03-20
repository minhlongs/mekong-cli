import { useState } from 'react';
import { Lead } from './types';
import { Dashboard } from './components/Dashboard';
import { LeadList } from './components/LeadList';
import { LeadForm } from './components/LeadForm';
import { LeadDetail } from './components/LeadDetail';
import { PipelineBoard } from './components/PipelineBoard';

type View = 'dashboard' | 'leads' | 'pipeline';
type FormMode = 'list' | 'create' | 'detail' | 'edit';

function App() {
  const [view, setView] = useState<View>('dashboard');
  const [formMode, setFormMode] = useState<FormMode>('list');
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [darkMode, setDarkMode] = useState(false);

  const handleSelectLead = (lead: Lead) => {
    setSelectedLead(lead);
    setFormMode('detail');
  };

  const handleStageFilter = () => {
    setView('leads');
  };

  const handleRefresh = () => {
    setFormMode('list');
    setSelectedLead(null);
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 dark:text-white">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <h1 className="text-2xl font-bold">CRM</h1>
            <nav className="flex gap-4">
              <button
                onClick={() => setView('dashboard')}
                className={`px-3 py-2 rounded ${view === 'dashboard' ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setView('leads')}
                className={`px-3 py-2 rounded ${view === 'leads' ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              >
                Leads
              </button>
              <button
                onClick={() => setView('pipeline')}
                className={`px-3 py-2 rounded ${view === 'pipeline' ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
              >
                Pipeline
              </button>
            </nav>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="btn btn-secondary"
              >
                {darkMode ? '☀️' : '🌙'}
              </button>
              {formMode === 'list' && view === 'leads' && (
                <button
                  onClick={() => setFormMode('create')}
                  className="btn btn-primary"
                >
                  + Add Lead
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          {view === 'dashboard' && (
            <>
              <Dashboard />
              <div className="mt-8">
                <h2 className="text-xl font-bold mb-4">Pipeline Overview</h2>
                <PipelineBoard onStageClick={handleStageFilter} />
              </div>
            </>
          )}

          {view === 'leads' && (
            <>
              {formMode === 'create' && (
                <LeadForm onSuccess={handleRefresh} onCancel={() => setFormMode('list')} />
              )}

              {formMode === 'list' && (
                <LeadList onSelectLead={handleSelectLead} onRefresh={handleRefresh} />
              )}

              {formMode === 'detail' && selectedLead && (
                <LeadDetail
                  lead={selectedLead}
                  onBack={() => setFormMode('list')}
                  onEdit={() => setFormMode('edit')}
                />
              )}

              {formMode === 'edit' && selectedLead && (
                <LeadForm
                  lead={selectedLead}
                  onSuccess={handleRefresh}
                  onCancel={() => setFormMode('detail')}
                />
              )}
            </>
          )}

          {view === 'pipeline' && (
            <div>
              <h2 className="text-xl font-bold mb-4">Pipeline by Stage</h2>
              <PipelineBoard onStageClick={handleStageFilter} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
