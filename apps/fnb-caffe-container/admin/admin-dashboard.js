/**
 * F&B Admin Dashboard - Orchestrator Module
 * Điều phối các module con: Orders, Analytics, Users
 * Kết nối API Dashboard và cập nhật real-time
 */

// Import các module con
import { ordersModule } from './admin-orders.js';
import { analyticsModule } from './admin-analytics.js';
import { usersModule } from './admin-users.js';

// ═══════════════════════════════════════════════════
//  CONFIG
// ═══════════════════════════════════════════════════
const REFRESH_INTERVAL = 30000; // 30 seconds

// ═══════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════
let dashboardState = {
  activeTab: 'dashboard',
  loading: false,
  lastUpdated: null
};

// ═══════════════════════════════════════════════════
//  DASHBOARD ORCHESTRATOR
// ═══════════════════════════════════════════════════
const adminDashboard = {
  /**
   * Khởi tạo dashboard chính
   */
  async init() {
    this.setupNavigation();
    this.setupGlobalEventListeners();
    await this.refreshAll();

    // Auto refresh
    setInterval(() => this.refreshAll(), REFRESH_INTERVAL);
  },

  /**
   * Làm mới tất cả dữ liệu
   */
  async refreshAll() {
    if (dashboardState.loading) return;

    dashboardState.loading = true;
    this.showLoading(true);

    try {
      // Refresh tất cả module
      await Promise.all([
        ordersModule.loadOrders(),
        analyticsModule.loadAnalytics()
      ]);

      dashboardState = {
        ...dashboardState,
        loading: false,
        lastUpdated: new Date()
      };

      this.updateLastUpdated();
    } catch (error) {
      console.error('Dashboard refresh error:', error);
      dashboardState.loading = false;
    } finally {
      this.showLoading(false);
    }
  },

  /**
   * Setup navigation giữa các tab
   */
  setupNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        navItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');

        const section = item.getAttribute('href').slice(1);
        this.navigateTo(section);
      });
    });
  },

  /**
   * Chuyển hướng giữa các section
   */
  navigateTo(section) {
    dashboardState.activeTab = section;

    // Ẩn tất cả sections
    const sections = ['dashboard', 'orders', 'analytics', 'menu', 'users', 'settings'];
    sections.forEach(s => {
      const el = document.getElementById(s);
      if (el) {
        el.style.display = s === section ? 'block' : 'none';
      }
    });

    // Load data cho section được chọn
    switch (section) {
      case 'dashboard':
        this.refreshAll();
        break;
      case 'orders':
        ordersModule.loadOrders();
        break;
      case 'analytics':
        analyticsModule.loadAnalytics();
        break;
      case 'users':
        usersModule.loadUsers();
        break;
    }
  },

  /**
   * Setup event listeners toàn cục
   */
  setupGlobalEventListeners() {
    // Refresh button
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshAll());
    }

    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      // F5 or Ctrl+R - Refresh
      if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
        e.preventDefault();
        this.refreshAll();
      }

      // Escape - Close modals
      if (e.key === 'Escape') {
        this.closeModals();
      }

      // Ctrl+1 - Dashboard
      if (e.ctrlKey && e.key === '1') {
        e.preventDefault();
        this.navigateTo('dashboard');
      }

      // Ctrl+2 - Orders
      if (e.ctrlKey && e.key === '2') {
        e.preventDefault();
        this.navigateTo('orders');
      }

      // Ctrl+3 - Analytics
      if (e.ctrlKey && e.key === '3') {
        e.preventDefault();
        this.navigateTo('analytics');
      }
    });
  },

  /**
   * Toggle dark/light theme
   */
  toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const icon = document.querySelector('.theme-icon');
    if (icon) {
      icon.textContent = document.body.classList.contains('dark-theme') ? '☀️' : '🌙';
    }
  },

  /**
   * Hiển thị loading overlay
   */
  showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
      overlay.style.display = show ? 'flex' : 'none';
    }
  },

  /**
   * Cập nhật thời gian last updated
   */
  updateLastUpdated() {
    const lastUpdatedEl = document.querySelector('.last-updated');
    if (lastUpdatedEl) {
      lastUpdatedEl.textContent = `Cập nhật: ${new Date().toLocaleTimeString('vi-VN')}`;
    }
  },

  /**
   * Đóng tất cả modals
   */
  closeModals() {
    const dialogs = document.querySelectorAll('md-dialog');
    dialogs.forEach(dialog => dialog.close());
  },

  /**
   * Hiển thị toast notification
   */
  showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed;
      top: 24px;
      right: 24px;
      padding: 16px 24px;
      border-radius: 8px;
      background: ${type === 'success' ? '#4CAF50' : '#f44336'};
      color: white;
      font-weight: 500;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 9999;
      animation: slideInRight 0.3s ease;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  },

  // Delegated methods cho các module con
  viewOrder: (orderId) => ordersModule.viewOrder(orderId),
  updateOrderStatus: (orderId, status) => ordersModule.updateOrderStatus(orderId, status),
  showOrderActions: (orderId) => ordersModule.showOrderActions(orderId),
  refreshData: () => adminDashboard.refreshAll()
};

// ═══════════════════════════════════════════════════
//  INITIALIZE
// ═══════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  // Khởi tạo dashboard orchestrator
  adminDashboard.init();

  // Khởi tạo các module con
  ordersModule.init();
  analyticsModule.init();
  usersModule.init();
});

// Export cho global access
window.admin = adminDashboard;
window.adminDashboard = adminDashboard;
window.ordersModule = ordersModule;
window.analyticsModule = analyticsModule;
window.usersModule = usersModule;
