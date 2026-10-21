// Cyber-Bento Horizon: Unified Multi-Page & Interactive Application Logic (stitch-kit)
document.addEventListener('DOMContentLoaded', () => {
  // All 21 registered screens in the synthetic Mekong Cyber-Bento demo (100% Vector SVG Icons)
  const ALL_SCREENS = [
    { href: 'index.html', title: '01 Landing — Public Marketing & Open-Core Hero', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>', group: 'Core' },
    { href: 'pricing.html', title: '02 Pricing — Transparent Pricing & Tier Matrix', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>', group: 'Core' },
    { href: 'cockpit.html', title: '03 Cockpit — Desktop Agent Cockpit & Swarm Topology', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>', group: 'Operations' },
    { href: 'billing.html', title: '04 Billing — Cloud Control Plane & MCU Meter', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>', group: 'Operations' },
    { href: 'audit.html', title: '05 Audit — Immutable Compliance Audit Ledger (SHA-256)', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>', group: 'Compliance' },
    { href: 'marketplace.html', title: '06 Marketplace — Strategy Recipe Marketplace & Creator Hub', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>', group: 'Recipes' },
    { href: 'settings.html', title: '07 Settings — Enterprise Multi-Tenant & Key Vault', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>', group: 'Operations' },
    { href: 'styleguide.html', title: '08 Styleguide — Component Style Guide & Primitives Catalog', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>', group: 'Design' },
    { href: 'docs.html', title: '09 Docs — Developer CLI & SDK Documentation Portal', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>', group: 'Core' },
    { href: 'playground.html', title: '10 Playground — WebAssembly Mekong CLI Sandbox', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>', group: 'Developer' },
    { href: 'invoice-verifier.html', title: '11 Invoice Verifier — Vietnamese TT78 / NĐ 123 E-Invoice Cryptographic Inspector', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>', group: 'Compliance' },
    { href: 'swarm-monitor.html', title: '12 Swarm Monitor — Real-time Distributed Swarm Visualizer & WebSocket Stream', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>', group: 'Operations' },
    { href: 'status.html', title: '13 Status — Global Microservice SLA, Cloud Daemon & Gateway Health', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>', group: 'Operations' },
    { href: 'recipe-builder.html', title: '14 Recipe Builder — Visual Drag-and-Drop Workflow & Swarm Strategy Studio', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>', group: 'Recipes' },
    { href: 'zalo-oa-console.html', title: '15 Zalo OA — Customer Engagement, Chatbot Orchestration & Campaign Console', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>', group: 'Integrations' },
    { href: 'agent-debugger.html', title: '16 Agent Debugger — In-Browser Interactive Debugger & Live DAG Visualizer', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>', group: 'Developer' },
    { href: 'vietqr-webhook-tester.html', title: '17 VietQR Tester — One-Click Deposit & Webhook Receiver Simulator', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>', group: 'Integrations' },
    { href: 'compliance-vault.html', title: '18 Compliance Vault — SOC-2 Evidence Inspector & Merkle Proof Browser', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>', group: 'Compliance' },
    { href: 'c-suite-boardroom.html', title: '19 C-Suite Boardroom — Executive War Room & OKR Telemetry', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="3" y1="22" x2="21" y2="22"/><line x1="6" y1="18" x2="6" y2="11"/><line x1="10" y1="18" x2="10" y2="11"/><line x1="14" y1="18" x2="14" y2="11"/><line x1="18" y1="18" x2="18" y2="11"/><polygon points="12 2 20 7 4 7"/></svg>', group: 'Executive' },
    { href: 'fintech-treasury.html', title: '20 Fintech Treasury — Multi-Bank VietQR & Cashflow Runway', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>', group: 'Fintech' },
    { href: 'zero-to-ipo-launchpad.html', title: '21 Zero-to-IPO Launchpad — Cap Table & SBV Compliance', icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="15" x2="15.01" y2="15"/></svg>', group: 'Executive' }
  ];

  // Client-Side Cryptographic Helper (Web Crypto API)
  async function computeSha256(text) {
    if (window.crypto && window.crypto.subtle) {
      const msgBuffer = new TextEncoder().encode(text);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', msgBuffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
    // Simple fallback
    return '0x' + Math.random().toString(16).substring(2).padEnd(64, '0');
  }

  // Demo API client. Payment and verification screens never mutate a live ledger.
  async function callCyberBentoApi(endpoint, method = 'GET', body = null) {
    try {
      const opts = {
        method,
        headers: { 'Content-Type': 'application/json' }
      };
      if (body) opts.body = JSON.stringify(body);
      const resp = await fetch(endpoint, opts);
      if (resp.ok) {
        return await resp.json();
      }
    } catch {
      // The public site is a demo surface; use explicit synthetic data if its API is unavailable.
    }

    // Client-side demo fallbacks
    if (endpoint.includes('/vietqr/simulate')) {
      const amt = body?.amount || 250000;
      return {
        success: true,
        simulated: true,
        demo_only: true,
        order_id: body?.order_id || `DEMO-${Date.now().toString().slice(-6)}`,
        amount_vnd: amt,
        simulated_mcu: Math.floor(amt / 1000),
        verified: false,
        notice: 'Demo only. No payment, webhook verification, or MCU credit was performed.',
        mode: 'demo_simulation'
      };
    }

    if (endpoint.includes('/tt78/verify')) {
      const invId = body?.invoice_id || 'INV-2026-009842';
      const hash = await computeSha256(`tt78:${invId}:${body?.amount_vnd || 15400000}`);
      return {
        demo_only: true,
        verified: false,
        invoice_id: invId,
        canonical_sha256: hash,
        compliance_standard: 'TT78 (Thông tư 78/2021/TT-BTC) & NĐ 123 (Nghị định 123/2020/NĐ-CP)',
        digital_stamp: `DEMO-HASH-ONLY-${hash.substring(0, 16).toUpperCase()}`
      };
    }

    if (endpoint.includes('/c-suite/quorum')) {
      return {
        demo_only: true,
        quorum_aligned: false,
        consensus_score: '0/5 (demo)',
        active_directive: 'No executive approval recorded in this demo.'
      };
    }

    if (endpoint.includes('/audit/merkle')) {
      const records = body?.records || ['demo_record:sample', 'demo_record:no_payment'];
      const hashes = await Promise.all(records.map(r => computeSha256(r)));
      const root = await computeSha256(hashes.join(''));
      return {
        merkle_root: root,
        leaf_count: records.length,
        demo_only: true,
        verified: false,
        demo_hash: `DEMO-HASH-ONLY-${root.substring(0, 16).toUpperCase()}`
      };
    }

    return { status: 'DEMO', demo_only: true, active_screens: 20 };
  }

  // Global Quick Nav Selector Listener
  const screenNavSelect = document.getElementById('screen-nav-select');
  if (screenNavSelect) {
    screenNavSelect.addEventListener('change', (e) => {
      const val = e.target.value;
      if (val && !val.startsWith('#')) {
        window.location.href = val;
      }
    });
  }

  // Global Hotkey Listener (Cmd+K / Ctrl+K & Escape)
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggleCommandPalette();
    }
    if (e.key === 'Escape') {
      closeAllModals();
    }
  });

  // Command Palette Elements & Filter Logic
  const cmdPalette = document.getElementById('cmd-palette-modal');
  const cmdInput = document.getElementById('cmd-palette-input');
  const cmdResults = document.getElementById('cmd-palette-results');

  function renderPaletteResults(query = '') {
    if (!cmdResults) return;
    cmdResults.replaceChildren();
    const q = query.trim().toLowerCase();
    const filtered = ALL_SCREENS.filter(s =>
      s.title.toLowerCase().includes(q) ||
      s.href.toLowerCase().includes(q) ||
      s.group.toLowerCase().includes(q)
    );

    if (filtered.length === 0) {
      const emptyDiv = document.createElement('div');
      emptyDiv.style.padding = '12px 16px';
      emptyDiv.style.color = 'var(--text-dim, #64748B)';
      emptyDiv.style.fontSize = '12px';
      emptyDiv.textContent = `No matching screens for "${query}"`;
      cmdResults.appendChild(emptyDiv);
      return;
    }

    filtered.forEach((s) => {
      const btn = document.createElement('a');
      btn.href = s.href;
      btn.className = 'btn btn-ghost cmd-palette-item';
      btn.style.display = 'flex';
      btn.style.alignItems = 'center';
      btn.style.justifyContent = 'space-between';
      btn.style.width = '100%';
      btn.style.padding = '8px 12px';
      btn.style.borderRadius = '6px';
      btn.style.textDecoration = 'none';
      btn.style.fontSize = '12px';
      btn.style.color = 'var(--text-main, #F8FAFC)';
      btn.style.textAlign = 'left';

      btn.innerHTML = `
        <span style="display:flex; align-items:center; gap:8px;">
          <span>${s.icon}</span>
          <span>${s.title}</span>
        </span>
        <span class="badge badge-cyan" style="font-size:10px; padding:2px 6px;">${s.group}</span>
      `;

      btn.addEventListener('mouseenter', () => {
        btn.style.background = 'var(--bg-hover, #181B26)';
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.background = 'transparent';
      });

      cmdResults.appendChild(btn);
    });
  }

  function toggleCommandPalette() {
    if (cmdPalette) {
      const isActive = cmdPalette.classList.contains('active');
      if (isActive) {
        cmdPalette.classList.remove('active');
      } else {
        cmdPalette.classList.add('active');
        if (cmdInput) {
          cmdInput.value = '';
          cmdInput.focus();
          renderPaletteResults('');
        }
      }
    }
  }

  if (cmdInput) {
    cmdInput.addEventListener('input', (e) => {
      renderPaletteResults(e.target.value);
    });

    cmdInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const firstLink = cmdResults?.querySelector('a.cmd-palette-item');
        if (firstLink) {
          window.location.href = firstLink.href;
        }
      }
    });
  }

  if (cmdPalette) {
    cmdPalette.addEventListener('click', (e) => {
      if (e.target === cmdPalette) {
        cmdPalette.classList.remove('active');
      }
    });
  }

  // VietQR payment-flow demonstration; this never changes a balance.
  const topUpModal = document.getElementById('modal-topup');
  const openModalBtns = document.querySelectorAll('.open-topup-trigger');
  const closeModalBtns = document.querySelectorAll('.close-topup-trigger');
  const simulatePayBtn = document.getElementById('simulate-pay-btn');
  const demoPaymentStatus = document.getElementById('demo-payment-status');
  openModalBtns.forEach(b => {
    b.addEventListener('click', () => {
      if (topUpModal) topUpModal.classList.add('active');
    });
  });

  if (topUpModal) {
    closeModalBtns.forEach(closeModalBtn => closeModalBtn.addEventListener('click', () => {
      topUpModal.classList.remove('active');
    }));
  }

  if (topUpModal) {
    topUpModal.addEventListener('click', (e) => {
      if (e.target === topUpModal) {
        topUpModal.classList.remove('active');
      }
    });
  }

  if (simulatePayBtn && demoPaymentStatus) {
    simulatePayBtn.addEventListener('click', async () => {
      demoPaymentStatus.textContent = 'Running a local demo simulation. No payment will be sent.';

      // Call API endpoint
      const result = await callCyberBentoApi('/api/v1/vietqr/simulate', 'POST', {
        amount: 250000,
        bank_code: 'VCB'
      });

      if (result?.simulated !== true || result?.demo_only !== true || result?.verified !== false) {
        demoPaymentStatus.textContent = 'Safe demo response unavailable. No payment or credit was processed.';
        return;
      }

      demoPaymentStatus.textContent = 'Demo complete. No bank payment, webhook verification, balance change, or ledger credit occurred.';
    });
  }

  // Interactive Live Triggers across screens
  // TT78 Invoice Verification Buttons
  const invoiceVerifyButtons = Array.from(document.querySelectorAll('button')).filter(btn =>
    btn.matches('[data-action="verify-tt78"]') || /verify invoice/i.test(btn.textContent || '')
  );
  invoiceVerifyButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      btn.textContent = 'Calculating demo hash...';
      const res = await callCyberBentoApi('/api/v1/tt78/verify', 'POST', {
        invoice_id: 'INV-2026-009842',
        seller_tax_id: '0312345678',
        amount_vnd: 15400000
      });
      alert(`Demo only. No invoice verification was performed.\nSample SHA-256: ${res.canonical_sha256 || res.hash_payload}\nDemo hash: ${res.digital_stamp}`);
      btn.textContent = 'Demo hash calculated';
    });
  });

  // Terminal Streaming Simulator
  const termBody = document.getElementById('terminal-stream');
  const startBtn = document.getElementById('btn-run-demo');
  if (startBtn && termBody) {
    const logs = [
      { text: '$ mekong init --open-core --clean-index', cls: 'cmd' },
      { text: '✓ Verified Open-Core boundary: apps/ & billing/ untracked', cls: 'success' },
      { text: '✓ 0 leaked API keys detected across 25 catalog checkpoints', cls: 'success' },
      { text: '> Initializing C-Suite Swarm topology (CEO, CTO, TaxEngine, PayOS)...', cls: 'cmd' },
      { text: '  [CEO] Dispatched quarterly strategic planning goal', cls: 'dim' },
      { text: '  [TaxEngine] TT78 digital invoice verification: 1,429 valid hashes', cls: 'dim' },
      { text: '  [PayOS] Polling VietQR gateway: HMAC-SHA256 signature verified', cls: 'success' },
      { text: '[WARN] Local free MCU units consumed: 10 / 10', cls: 'warn' },
      { text: 'HTTP 402 Payment Required: Quota exhausted. Cloud daemon sync required.', cls: 'warn' },
      { text: '> Ready for Cloud Control Plane top-up [Cmd+K -> Top Up]', cls: 'cmd' }
    ];

    startBtn.addEventListener('click', () => {
      termBody.replaceChildren();
      logs.forEach((item, index) => {
        setTimeout(() => {
          const div = document.createElement('div');
          div.className = `terminal-line ${item.cls}`;
          div.textContent = item.text;
          termBody.appendChild(div);
          termBody.scrollTop = termBody.scrollHeight;
        }, index * 260);
      });
    });
  }

  // Global exports for inline handlers
  window.toggleCommandPalette = toggleCommandPalette;
  window.closeAllModals = function() {
    if (topUpModal) topUpModal.classList.remove('active');
    if (cmdPalette) cmdPalette.classList.remove('active');
  };
  window.MekongAPI = {
    call: callCyberBentoApi,
    computeSha256,
    screens: ALL_SCREENS
  };
});
