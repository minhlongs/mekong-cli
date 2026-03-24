/**
 * F&B Caffe Container — Admin Dashboard Orchestrator
 * Main entry point that coordinates dashboard modules
 *
 * Modules:
 * - charts.js: Chart rendering and visualization
 * - data-fetcher.js: API data fetching
 * - filters.js: Filter, search, pagination, export
 */

// Import modules (ES modules syntax for browser)
import {
    renderStats,
    renderRevenueChart,
    renderOrdersTable,
    renderTopProducts,
    translatePaymentStatus,
    translateOrderStatus
} from './charts.js';

import {
    fetchStats,
    fetchRevenue,
    fetchOrders,
    fetchOrderDetail,
    fetchTopProducts,
    updateOrderStatus
} from './data-fetcher.js';

import {
    filterOrders,
    calculateDateRange,
    createPagination,
    exportData,
    initializeSearch,
    initializeFilters,
    initializeExport
} from './filters.js';

// Dashboard State
const DashboardState = {
    currentPage: 1,
    totalPages: 1,
    currentFilter: 'all',
    dateRange: { start: null, end: null },
    searchQuery: '',
    orders: [],
    stats: null
};

// Export state for modules to access
window.DashboardState = DashboardState;

/**
 * Initialize Dashboard
 */
function initializeDashboard() {
    // Load dashboard data
    loadDashboardData();

    // Initialize search with debounce
    initializeSearch((query) => {
        DashboardState.searchQuery = query;
        filterAndRenderOrders();
    });

    // Initialize filters
    initializeFilters({
        onStatusFilter: (filter) => {
            DashboardState.currentFilter = filter;
            loadOrders();
        },
        onDateRangeFilter: (dates) => {
            DashboardState.dateRange = dates;
            loadDashboardData();
        }
    });

    // Initialize export buttons
    initializeExport(DashboardState.orders);

    // Initialize real-time refresh
    initializeRealTimeRefresh();

    // Sidebar Toggle (Mobile)
    setupSidebarToggle();

    // Navigation Active State
    setupNavigation();

    // Stats Card Hover Animation
    setupStatCardAnimations();
}

/**
 * Load Dashboard Data
 */
async function loadDashboardData() {
    // Show skeletons
    const statsGrid = document.querySelector('.stats-grid');
    if (statsGrid) {
        Skeleton.show(statsGrid, 'card', 4);
    }

    // Load stats
    const stats = await fetchStats(7);
    if (stats) {
        DashboardState.stats = stats;
        renderStats(stats);
    }

    // Load revenue chart
    const revenueData = await fetchRevenue(7);
    if (revenueData.length > 0) {
        renderRevenueChart(revenueData);
    }

    // Load orders table
    await loadOrders();

    // Load top products
    const products = await fetchTopProducts(5);
    if (products.length > 0) {
        renderTopProducts(products);
    }

    // Hide skeletons
    if (statsGrid) {
        Skeleton.hide(statsGrid);
    }
}

/**
 * Load Orders with Pagination
 */
async function loadOrders() {
    const tableBody = document.querySelector('.orders-table tbody');
    if (!tableBody) return;

    // Show skeleton
    Skeleton.show(tableBody.parentElement, 'table', 5);

    try {
        const orders = await fetchOrders(
            DashboardState.currentFilter === 'all' ? null : DashboardState.currentFilter,
            20,
            DashboardState.currentPage
        );

        DashboardState.orders = orders;

        if (orders.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-dim);">
                        Không có đơn hàng nào
                    </td>
                </tr>
            `;
        } else {
            renderOrdersTable(orders);
        }

        updatePagination();
    } catch (error) {
        if (window.Toast) {
            Toast.error('Không thể tải danh sách đơn hàng');
        }
    }

    // Hide skeleton
    Skeleton.hide(tableBody.parentElement);
}

/**
 * Filter and Render Orders (for search)
 */
function filterAndRenderOrders() {
    const filtered = filterOrders(DashboardState.orders, DashboardState.searchQuery);
    renderOrdersTable(filtered);
}

/**
 * Update Pagination
 */
function updatePagination() {
    const paginationContainer = document.querySelector('.pagination-container');
    if (!paginationContainer) return;

    paginationContainer.innerHTML = '';
    const pagination = createPagination({
        currentPage: DashboardState.currentPage,
        totalPages: DashboardState.totalPages,
        onPageChange: (page) => {
            DashboardState.currentPage = page;
            loadOrders();
        }
    });
    paginationContainer.appendChild(pagination);
}

/**
 * Initialize Real-time Refresh
 */
function initializeRealTimeRefresh() {
    // Auto-refresh every 60 seconds
    setInterval(() => {
        refreshData();
    }, 60000);
}

/**
 * Refresh Data
 */
function refreshData() {
    // Animate stat values
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(stat => {
        stat.style.transition = 'opacity 0.3s';
        stat.style.opacity = '0.5';
        setTimeout(() => {
            stat.style.opacity = '1';
        }, 300);
    });

    // Reload data
    loadDashboardData();

    if (window.Toast) {
        Toast.info('Dữ liệu đã được làm mới', 2000);
    }
}

/**
 * Setup Sidebar Toggle
 */
function setupSidebarToggle() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Close sidebar when clicking outside (mobile)
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });
}

/**
 * Setup Navigation Active State
 */
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Allow navigation
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
            }

            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            // Update page title based on navigation
            const pageLabel = this.querySelector('.nav-label');
            if (pageLabel) {
                const pageTitle = document.querySelector('.page-title');
                if (pageTitle) {
                    pageTitle.textContent = pageLabel.textContent;
                }
            }
        });
    });
}

/**
 * Setup Stat Card Hover Animations
 */
function setupStatCardAnimations() {
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            statCards.forEach(c => {
                if (c !== card) {
                    c.style.opacity = '0.7';
                }
            });
        });

        card.addEventListener('mouseleave', function() {
            statCards.forEach(c => {
                c.style.opacity = '1';
            });
        });
    });
}

// ─── Dark Mode Theme Toggle ───
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = themeToggle?.querySelector('.theme-icon') || themeToggle;

    if (!themeToggle) return;

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

// ─── Order Detail Modal ───
/**
 * Show Order Detail Modal
 * @param {number} orderId - Order ID to display
 */
async function showOrderDetail(orderId) {
    try {
        const order = await fetchOrderDetail(orderId);
        if (!order) {
            if (window.Toast) {
                Toast.error('Không thể tải chi tiết đơn hàng');
            }
            return;
        }

        const content = `
            <div class="order-detail-grid">
                <div class="order-detail-section">
                    <h4>Thông tin đơn hàng</h4>
                    <div class="order-info-row">
                        <span class="order-info-label">Mã đơn</span>
                        <span class="order-info-value">#${order.id}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Ngày đặt</span>
                        <span class="order-info-value">${formatDate(new Date(order.created_at))}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Tổng tiền</span>
                        <span class="order-info-value">${formatCurrency(order.total)}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Phương thức thanh toán</span>
                        <span class="order-info-value">${order.payment_method || 'Tiền mặt'}</span>
                    </div>
                </div>

                <div class="order-detail-section">
                    <h4>Thông tin khách hàng</h4>
                    <div class="order-info-row">
                        <span class="order-info-label">Tên khách</span>
                        <span class="order-info-value">${order.customer?.full_name || 'N/A'}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Số điện thoại</span>
                        <span class="order-info-value">${order.customer?.phone || 'N/A'}</span>
                    </div>
                    <div class="order-info-row">
                        <span class="order-info-label">Email</span>
                        <span class="order-info-value">${order.customer?.email || 'N/A'}</span>
                    </div>
                </div>
            </div>

            <div class="order-detail-section">
                <h4>Sản phẩm</h4>
                <div class="order-items-list">
                    ${order.items?.map(item => `
                        <div class="order-item-row">
                            <div class="order-item-qty">x${item.quantity}</div>
                            <span class="order-item-name">${item.name}</span>
                            <span class="order-item-price">${formatCurrency(item.price * item.quantity)}</span>
                        </div>
                    `).join('') || '<p style="color: var(--text-dim);">Không có sản phẩm</p>'}
                </div>
            </div>

            <div class="status-actions">
                ${order.order_status === 'pending' ? `
                    <button class="btn btn-primary" onclick="handleOrderAction(${order.id}, 'confirm')">Xác nhận</button>
                    <button class="btn btn-danger" onclick="handleOrderAction(${order.id}, 'cancel')">Hủy đơn</button>
                ` : ''}
                ${order.order_status === 'confirmed' ? `
                    <button class="btn btn-primary" onclick="handleOrderAction(${order.id}, 'prepare')">Chuẩn bị</button>
                ` : ''}
                ${order.order_status === 'preparing' ? `
                    <button class="btn btn-primary" onclick="handleOrderAction(${order.id}, 'ready')">Sẵn sàng</button>
                ` : ''}
                ${order.order_status === 'ready' ? `
                    <button class="btn btn-primary" onclick="handleOrderAction(${order.id}, 'deliver')">Giao hàng</button>
                ` : ''}
            </div>
        `;

        if (window.Modal) {
            Modal.show({
                title: `Chi tiết đơn hàng #${order.id}`,
                content,
                size: 'large',
                actions: [
                    {
                        id: 'close',
                        label: 'Đóng',
                        variant: 'secondary',
                        onClick: () => {},
                        close: false
                    }
                ]
            });
        }
    } catch (error) {
        if (window.Toast) {
            Toast.error('Không thể tải chi tiết đơn hàng');
        }
    }
}

/**
 * Handle Order Action
 * @param {number} orderId - Order ID
 * @param {string} action - Action to perform
 */
async function handleOrderAction(orderId, action) {
    const actions = {
        view: () => showOrderDetail(orderId),
        confirm: { label: 'Xác nhận', apiAction: 'confirm' },
        cancel: { label: 'Hủy', apiAction: 'cancel', confirm: true },
        prepare: { label: 'Chuẩn bị', apiAction: 'prepare' },
        ready: { label: 'Sẵn sàng', apiAction: 'ready' },
        deliver: { label: 'Giao hàng', apiAction: 'deliver' }
    };

    const actionConfig = actions[action];
    if (!actionConfig) return;

    // Confirm destructive actions
    if (actionConfig.confirm) {
        if (window.Confirm) {
            const confirmed = await Confirm.show({
                title: 'Xác nhận hủy đơn',
                message: 'Bạn có chắc chắn muốn hủy đơn hàng này? Hành động này không thể hoàn tác.',
                confirmLabel: 'Hủy đơn',
                cancelLabel: 'Quay lại',
                type: 'danger'
            });

            if (!confirmed) return;
        }
    }

    try {
        const result = await updateOrderStatus(orderId, actionConfig.apiAction);
        if (result) {
            if (window.Toast) {
                Toast.success(`Đã ${actionConfig.label.toLowerCase()} đơn hàng #${orderId}`);
            }
            loadOrders();
            loadDashboardData();
        } else {
            if (window.Toast) {
                Toast.error('Có lỗi xảy ra khi cập nhật đơn hàng');
            }
        }
    } catch (error) {
        if (window.Toast) {
            Toast.error('Có lỗi xảy ra khi cập nhật đơn hàng');
        }
    }
}

// ─── Utility Functions ───

/**
 * Format currency in Vietnamese Dong
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(amount);
}

/**
 * Format date in Vietnamese
 * @param {Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('vi-VN', {
        weekday: 'short',
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Debounce function for search inputs
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ─── Export for use in other modules ───
window.DashboardUtils = {
    formatCurrency,
    formatDate,
    debounce
};

// ─── Make functions globally accessible ───
window.showOrderDetail = showOrderDetail;
window.handleOrderAction = handleOrderAction;

// ─── Export Data Function ───
function exportData(data, filename) {
  const headers = ['ID', 'Customer', 'Phone', 'Total', 'Status', 'Date'];
  const csvContent = [
    headers.join(','),
    ...data.map(order => [
      order.id,
      order.customer?.full_name || '',
      order.customer?.phone || '',
      order.total,
      order.order_status,
      order.created_at
    ].join(','))
  ].join('\\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename || 'orders.csv';
  link.click();
}

function exportToCSV(data) {
  exportData(data, 'dashboard-export.csv');
}

// ─── Mock Data Methods for Testing ───
function getMockStats() {
  return {
    revenue: 10000000,
    orders: 50,
    customers: 30,
    products: 20
  };
}

function getMockRevenue() {
  return [
    { date: '2026-03-18', revenue: 5000000 },
    { date: '2026-03-19', revenue: 7000000 },
    { date: '2026-03-20', revenue: 6000000 },
    { date: '2026-03-21', revenue: 8000000 },
    { date: '2026-03-22', revenue: 9000000 },
    { date: '2026-03-23', revenue: 10000000 },
    { date: '2026-03-24', revenue: 11000000 }
  ];
}

function getMockOrders() {
  return [
    { id: 1, customer: { full_name: 'Nguyen Van A', phone: '0901234567' }, total: 100000, order_status: 'completed', created_at: '2026-03-24' },
    { id: 2, customer: { full_name: 'Tran Thi B', phone: '0912345678' }, total: 150000, order_status: 'pending', created_at: '2026-03-24' },
    { id: 3, customer: { full_name: 'Le Van C', phone: '0923456789' }, total: 200000, order_status: 'processing', created_at: '2026-03-23' }
  ];
}

function getMockTopProducts() {
  return [
    { id: 1, name: 'Espresso', quantity: 100, revenue: 2900000 },
    { id: 2, name: 'Capuchino', quantity: 80, revenue: 3920000 },
    { id: 3, name: 'Tra Dao', quantity: 60, revenue: 2700000 }
  ];
}

// ─── Search Input Handler ───
function initSearchInput() {
  const searchInput = document.getElementById('globalSearch');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.trim();
      DashboardState.searchQuery = query;
      filterAndRenderOrders();
    });
  }
}

// ─── Initialize on DOM Ready ───
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    initThemeToggle();
    initSearchInput();
});

// ─── Keyboard Shortcuts ───
document.addEventListener('keydown', (e) => {
    // Escape key to close modals
    if (e.key === 'Escape') {
        const modal = document.querySelector('.modal.active');
        if (modal && window.Modal) {
            Modal.close();
        }
    }

    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }
});
