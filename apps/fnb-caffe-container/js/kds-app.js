// ═══════════════════════════════════════════════
//  KITCHEN DISPLAY SYSTEM (KDS) — Orchestrator
//  F&B Container Café — Sa Đéc
//  Modular architecture: orders, display, timer
// ═══════════════════════════════════════════════

import {
  KDS_STATE,
  KDS_CONFIG,
  loadOrders,
  saveOrders,
  advanceOrderStatus,
  moveToPreviousStatus,
  updateStats,
  initSettings,
  generateRandomOrder
} from './kds-orders.js';

import {
  renderAllOrders,
  handleNewOrder,
  showAlert,
  playNotificationSound,
  openSettingsModal,
  closeSettingsModal,
  closeOrderDetailModal
} from './kds-display.js';

import {
  updateClock,
  updateTimers
} from './kds-timer.js';

// ─── API Configuration ───
const KDS_CONFIG_LOCAL = {
  API_BASE: 'http://localhost:8000/api',
  WS_URL: 'ws://localhost:8080/ws',
  POLL_INTERVAL: 5000,
  SOUND_ENABLED: true,
  AUTO_REFRESH: true
};

// Expose functions globally for onclick handlers
window.KDS_HANDLERS = {
  advanceOrderStatus,
  moveToPreviousStatus
};

// ─── API Functions ───
async function fetchKDSOrders() {
  try {
    const response = await fetch(`${KDS_CONFIG_LOCAL.API_BASE}/kds/orders`);
    const result = await response.json();

    if (result.success) {
      const previousCount = KDS_STATE.orders.length;
      KDS_STATE.orders = result.orders;
      KDS_STATE.settings.lastSync = result.lastUpdated;

      if (result.orders.length > previousCount) {
        const newOrder = result.orders[result.orders.length - 1];
        handleNewOrder(newOrder);
      }

      KDS_STATE.lastOrderCount = result.orders.length;
      saveOrders();
      renderAllOrders();
      updateStats();
    }
  } catch (error) {
    loadOrders();
    renderAllOrders();
  }
}

async function fetchKDSStats() {
  try {
    const response = await fetch(`${KDS_CONFIG_LOCAL.API_BASE}/kds/stats`);
    const result = await response.json();

    if (result.success) {
      KDS_STATE.stats = result.stats;
      document.getElementById('statPending').textContent = result.stats.pending;
      document.getElementById('statPreparing').textContent = result.stats.preparing;
      document.getElementById('statReady').textContent = result.stats.ready;
    }
  } catch (error) {
    // Silently fail
  }
}

// ─── Check New Orders ───
function checkNewOrders() {
  const currentCount = KDS_STATE.orders.length;

  if (currentCount > KDS_STATE.lastOrderCount) {
    const newOrder = KDS_STATE.orders[currentCount - 1];
    handleNewOrder(newOrder);
  }

  KDS_STATE.lastOrderCount = currentCount;
}

// ─── Settings Handlers ───
function setupSettingsHandlers(btnGenerateTest, btnViewAll) {
  if (btnGenerateTest) {
    btnGenerateTest.addEventListener('click', () => {
      const newOrder = generateRandomOrder();
      KDS_STATE.orders.push(newOrder);
      saveOrders();
      renderAllOrders();
      updateStats();
      showAlert(newOrder);
      if (KDS_STATE.settings.soundEnabled) {
        playNotificationSound();
      }
      closeSettingsModal();
    });
  }

  if (btnViewAll) {
    btnViewAll.addEventListener('click', () => {
      const report = KDS_STATE.orders.map(o => `${o.id} - ${o.status} - ${KDS_STATE.orders.constructor.prototype.formatCurrency ? KDS_STATE.orders.constructor.prototype.formatCurrency(o.total) : o.total}`).join('\n');
      alert(`Tất cả Orders:\n\n${report}`);
    });
  }
}

// ─── Initialization ───
async function initKDS() {
  await fetchKDSOrders();
  await fetchKDSStats();

  if (KDS_STATE.orders.length === 0) {
    loadOrders();
    renderAllOrders();
  }

  updateClock();

  // Clock update every second
  setInterval(updateClock, 1000);

  // Timer update every second
  setInterval(updateTimers, 1000);

  // Auto-refresh orders from API
  setInterval(() => {
    if (KDS_STATE.settings.autoRefresh) {
      fetchKDSOrders();
      fetchKDSStats();
    }
  }, KDS_STATE.settings.refreshInterval);

  // Check for new orders periodically
  setInterval(checkNewOrders, 2000);

  // Modal handlers
  document.getElementById('kdsSettings')?.addEventListener('click', openSettingsModal);
  document.getElementById('kdsModalClose')?.addEventListener('click', closeSettingsModal);
  document.getElementById('orderDetailClose')?.addEventListener('click', closeOrderDetailModal);
  document.getElementById('alertDismiss')?.addEventListener('click', () => {
    document.getElementById('orderAlert').classList.remove('show');
  });

  // Close modals on overlay click
  document.querySelectorAll('.kds-modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', () => {
      document.querySelectorAll('.kds-modal').forEach(m => m.classList.remove('show'));
    });
  });

  // Settings
  const { btnGenerateTest, btnViewAll } = initSettings();
  setupSettingsHandlers(btnGenerateTest, btnViewAll);
}

// ─── Theme Toggle (local copy for KDS) ───
function initThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = themeToggle?.querySelector('.theme-icon') || themeToggle;

  if (!themeToggle) {return;}

  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);

  if (themeIcon) {
    themeIcon.textContent = savedTheme === 'dark' ? '🌙' : '☀️';
  }

  themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    if (themeIcon) {
      themeIcon.textContent = newTheme === 'dark' ? '🌙' : '☀️';
    }
  });
}

// Start KDS
document.addEventListener('DOMContentLoaded', () => {
  initKDS();
  initThemeToggle();
});

// ─── Export Functions to Window for Test Compatibility ───
window.advanceOrderStatus = advanceOrderStatus;
window.moveToPreviousStatus = moveToPreviousStatus;
