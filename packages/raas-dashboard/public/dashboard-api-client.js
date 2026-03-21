/**
 * RaaS Admin Dashboard — API client + data renderers
 * Auth: X-Admin-Key header (set via login form, stored in localStorage)
 */

let cfg = { url: '', key: '' };
let refreshTimer = null;

// --- Auth helpers ---

export function loadSavedConfig() {
  const url = localStorage.getItem('raas_url');
  const key = localStorage.getItem('raas_key');
  if (url && key) { cfg = { url, key }; return true; }
  return false;
}

export function saveConfig(url, key) {
  cfg = { url: url.replace(/\/$/, ''), key };
  localStorage.setItem('raas_url', cfg.url);
  localStorage.setItem('raas_key', cfg.key);
}

export function clearConfig() {
  localStorage.removeItem('raas_url');
  localStorage.removeItem('raas_key');
  cfg = { url: '', key: '' };
  clearInterval(refreshTimer);
}

// --- Fetch helper ---

async function apiFetch(path) {
  const r = await fetch(cfg.url + path, { headers: { 'X-Admin-Key': cfg.key } });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText} — ${path}`);
  return r.json();
}

// --- Renderers ---

export async function renderOverview() {
  const d = await apiFetch('/admin/stats');
  const t = d.tenants || {}; const m = d.missions || {}; const c = d.credits || {};
  const mrr = ((c.totalEarned || 0) / 100).toFixed(0);
  const n = v => Number(v||0).toLocaleString();
  document.getElementById('overview-cards').innerHTML = `
    <div class="card"><div class="label">Total Tenants</div><div class="val">${n(t.total)}</div><div class="sub">${n(t.active)} active</div></div>
    <div class="card"><div class="label">Total Missions</div><div class="val">${n(m.total)}</div><div class="sub">${n(m.completed)} completed · ${n(m.failed)} failed</div></div>
    <div class="card"><div class="label">Credits Sold</div><div class="val">${n(c.totalEarned)}</div><div class="sub">${n(c.totalSpent)} spent</div></div>
    <div class="card"><div class="label">MRR Est.</div><div class="val">$${n(mrr)}</div><div class="sub">credits × $0.01</div></div>`;
}

export async function renderTenants() {
  const d = await apiFetch('/v1/tenants?limit=50');
  const rows = d.tenants || d.data || (Array.isArray(d) ? d : []);
  if (!rows.length) { document.getElementById('tenants-body').innerHTML = '<div class="loading">No tenants found.</div>'; return; }
  document.getElementById('tenants-body').innerHTML = `<table>
    <thead><tr><th>Name</th><th>Email</th><th>Tier</th><th>Balance</th><th>Status</th><th>Created</th></tr></thead>
    <tbody>${rows.map(r => `<tr>
      <td>${esc(r.name||'—')}</td><td>${esc(r.email||'—')}</td>
      <td><span class="badge ok">${esc(r.tier||'free')}</span></td>
      <td>${(r.balance||0).toLocaleString()}</td>
      <td><span class="badge ${r.active||r.status==='active'?'ok':'warn'}">${r.active||r.status==='active'?'active':'inactive'}</span></td>
      <td>${fmtDate(r.created_at)}</td></tr>`).join('')}</tbody></table>`;
}

export async function renderMissions() {
  const d = await apiFetch('/v1/missions?limit=50');
  const rows = d.missions || d.data || (Array.isArray(d) ? d : []);
  if (!rows.length) { document.getElementById('missions-body').innerHTML = '<div class="loading">No missions found.</div>'; return; }
  document.getElementById('missions-body').innerHTML = `<table>
    <thead><tr><th>ID</th><th>Type</th><th>Status</th><th>Credits</th><th>Created</th></tr></thead>
    <tbody>${rows.map(r => `<tr>
      <td style="font-family:monospace;font-size:.75rem">${esc((r.id||'').slice(0,8))}…</td>
      <td>${esc(r.type||r.mission_type||'—')}</td>
      <td><span class="badge ${statusBadge(r.status)}">${esc(r.status||'—')}</span></td>
      <td>${r.credits||r.cost||0}</td>
      <td>${fmtDate(r.created_at)}</td></tr>`).join('')}</tbody></table>`;
}

export async function renderCredits() {
  const d = await apiFetch('/credits/ledger?limit=50');
  const rows = d.transactions || d.data || (Array.isArray(d) ? d : []);
  if (!rows.length) { document.getElementById('credits-body').innerHTML = '<div class="loading">No ledger entries found.</div>'; return; }
  document.getElementById('credits-body').innerHTML = `<table>
    <thead><tr><th>Tenant</th><th>Type</th><th>Amount</th><th>Balance After</th><th>Created</th></tr></thead>
    <tbody>${rows.map(r => `<tr>
      <td>${esc(r.tenant_id||'—')}</td>
      <td><span class="badge ${r.type==='purchase'?'ok':'warn'}">${esc(r.type||'—')}</span></td>
      <td style="color:${(r.amount||0)>=0?'var(--success)':'var(--err)'}">${(r.amount||0)>=0?'+':''}${r.amount||0}</td>
      <td>${r.balance_after||r.balance||0}</td>
      <td>${fmtDate(r.created_at)}</td></tr>`).join('')}</tbody></table>`;
}

// --- Utilities ---

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function fmtDate(s) { if (!s) return '—'; try { return new Date(s).toLocaleDateString(); } catch { return s; } }
function statusBadge(s) { return s==='completed'?'ok':s==='failed'?'err':'warn'; }

// --- Auto-refresh orchestrator ---

export async function refreshAll() {
  document.getElementById('last-refresh').textContent = 'Refreshing…';
  try {
    await Promise.all([renderOverview(), renderTenants(), renderMissions(), renderCredits()]);
    document.getElementById('last-refresh').textContent = 'Updated ' + new Date().toLocaleTimeString();
    document.getElementById('error-banner').style.display = 'none';
  } catch (e) {
    const b = document.getElementById('error-banner');
    b.textContent = 'Fetch error: ' + e.message;
    b.style.display = 'block';
    document.getElementById('last-refresh').textContent = 'Error';
  }
}

export function startAutoRefresh() {
  refreshAll();
  refreshTimer = setInterval(refreshAll, 30000);
}
