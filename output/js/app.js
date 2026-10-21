// Cyber-Bento Horizon: Interactive Application Logic (stitch-kit)
document.addEventListener('DOMContentLoaded', () => {
  // Navigation Router
  const navTabs = document.querySelectorAll('.nav-tab-btn');
  const screenSections = document.querySelectorAll('.screen-view');

  function switchTab(targetId) {
    navTabs.forEach(t => {
      if (t.dataset.screen === targetId) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });

    screenSections.forEach(s => {
      if (s.id === targetId) {
        s.style.display = 'block';
      } else {
        s.style.display = 'none';
      }
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      switchTab(tab.dataset.screen);
    });
  });

  // Global Hotkey Listener
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggleCommandPalette();
    }
    if (e.key === 'Escape') {
      closeAllModals();
    }
  });

  // Terminal Streaming Simulator
  const termBody = document.getElementById('terminal-stream');
  const startBtn = document.getElementById('btn-run-demo');
  if (startBtn && termBody) {
    const logs = [
      { text: '$ mekong init --open-core --clean-index', cls: 'cmd' },
      { text: '✓ Verified Open-Core boundary: apps/ & billing/ untracked', cls: 'success' },
      { text: '✓ 0 leaked API keys detected across 25 catalog checkpoints', cls: 'success' },
      { text: '⚡ Initializing C-Suite Swarm topology (CEO, CTO, TaxEngine, PayOS)...', cls: 'cmd' },
      { text: '  [CEO] Dispatched quarterly strategic planning goal', cls: 'dim' },
      { text: '  [TaxEngine] TT78 digital invoice verification: 1,429 valid hashes', cls: 'dim' },
      { text: '  [PayOS] Polling VietQR gateway: HMAC-SHA256 signature verified', cls: 'success' },
      { text: '⚡ Local free MCU units consumed: 10 / 10', cls: 'warn' },
      { text: 'HTTP 402 Payment Required: Quota exhausted. Cloud daemon sync required.', cls: 'warn' },
      { text: '⚡ Ready for Cloud Control Plane top-up [Cmd+K -> Top Up]', cls: 'cmd' }
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

  // PayOS VietQR Modal & Live Top-up Polling
  const topUpModal = document.getElementById('modal-topup');
  const openModalBtns = document.querySelectorAll('.open-topup-trigger');
  const closeModalBtn = document.getElementById('btn-close-modal');
  const confirmPayBtn = document.getElementById('btn-confirm-pay');
  const qrPollingStatus = document.getElementById('qr-polling-indicator');
  const balanceDisplay = document.getElementById('mcu-balance-value');

  let currentBalance = 9420;

  openModalBtns.forEach(b => {
    b.addEventListener('click', () => {
      if (topUpModal) topUpModal.classList.add('active');
    });
  });

  if (closeModalBtn && topUpModal) {
    closeModalBtn.addEventListener('click', () => {
      topUpModal.classList.remove('active');
    });
  }

  if (confirmPayBtn && qrPollingStatus) {
    confirmPayBtn.addEventListener('click', () => {
      qrPollingStatus.style.color = '#f59e0b';
      qrPollingStatus.textContent = '⏳ Simulating VietQR payment receipt...';
      setTimeout(() => {
        currentBalance += 250;
        if (balanceDisplay) balanceDisplay.textContent = currentBalance.toLocaleString();
        qrPollingStatus.style.color = '#10b981';
        qrPollingStatus.textContent = '✓ Webhook confirmed (HMAC-SHA256)! 250 MCU Credited.';
        setTimeout(() => {
          topUpModal.classList.remove('active');
          qrPollingStatus.style.color = 'var(--text-dim)';
          qrPollingStatus.textContent = '⚡ Waiting for banking app scan...';
          alert('🎉 Payment Successful! 250 MCU credited to workspace ledger.');
        }, 1200);
      }, 1500);
    });
  }

  // Pricing Matrix Currency & Burn Calculator
  const currencyToggle = document.getElementById('currency-toggle');
  const slider = document.getElementById('agent-slider');
  const estimatedMcu = document.getElementById('calc-mcu-burn');
  const estimatedVnd = document.getElementById('calc-vnd-burn');

  if (slider && estimatedMcu && estimatedVnd) {
    slider.addEventListener('input', (e) => {
      const agents = parseInt(e.target.value, 10);
      document.getElementById('agent-count-val').textContent = agents;
      const mcu = agents * 125;
      const vnd = mcu * 1000;
      estimatedMcu.textContent = `${mcu.toLocaleString()} MCU / mo`;
      estimatedVnd.textContent = `${vnd.toLocaleString()} VND / mo`;
    });
  }

  // Command Palette
  const cmdPalette = document.getElementById('cmd-palette-modal');
  function toggleCommandPalette() {
    if (cmdPalette) {
      cmdPalette.classList.toggle('active');
      const input = document.getElementById('cmd-palette-input');
      if (cmdPalette.classList.contains('active') && input) {
        input.focus();
      }
    }
  }

  window.toggleCommandPalette = toggleCommandPalette;
  window.switchTab = switchTab;

  function closeAllModals() {
    if (topUpModal) topUpModal.classList.remove('active');
    if (cmdPalette) cmdPalette.classList.remove('active');
  }
});
