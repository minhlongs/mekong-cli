/**
 * Kitchen Display System (KDS) Tests - F&B Caffe Container
 */

const fs = require('fs');
const path = require('path');

const rootDir = path.join(__dirname, '..');

describe('Kitchen Display System', () => {
    let kdsHtml;
    let kdsOrdersJs;
    let kdsOrdersJs;

    beforeAll(() => {
        kdsHtml = fs.readFileSync(path.join(rootDir, 'kitchen-display.html'), 'utf8');
        kdsOrdersJs = fs.readFileSync(path.join(rootDir, 'js/kds-app.js'), 'utf8');
        kdsOrdersJs = fs.readFileSync(path.join(rootDir, 'js/kds-orders.js'), 'utf8');
    });

    describe('HTML Structure', () => {
        test('should have valid HTML5 structure', () => {
            expect(kdsHtml).toContain('<!DOCTYPE html>');
            expect(kdsHtml).toContain('<html lang="vi">');
            expect(kdsHtml).toContain('<head>');
            expect(kdsHtml).toContain('<body class="kds-body">');
        });

        test('should have proper charset and viewport', () => {
            expect(kdsHtml).toContain('charset="UTF-8"');
            expect(kdsHtml).toContain('name="viewport"');
            expect(kdsHtml).toContain('width=device-width');
        });

        test('should have KDS title', () => {
            expect(kdsHtml).toContain('<title>Kitchen Display System');
        });

        test('should have robots noindex for SEO', () => {
            expect(kdsHtml).toContain('name="robots"');
            expect(kdsHtml).toContain('noindex, nofollow');
        });

        test('should have chef emoji favicon', () => {
            expect(kdsHtml).toContain('rel="icon"');
            expect(kdsHtml).toContain('👨‍🍳');
        });
    });

    describe('KDS Header', () => {
        test('should have header with kds-header class', () => {
            expect(kdsHtml).toContain('class="kds-header"');
        });

        test('should have KDS logo', () => {
            expect(kdsHtml).toContain('class="kds-logo"');
            expect(kdsHtml).toContain('👨‍🍳');
        });

        test('should have title and subtitle', () => {
            expect(kdsHtml).toContain('class="kds-title"');
            expect(kdsHtml).toContain('Kitchen Display System');
            expect(kdsHtml).toContain('class="kds-subtitle"');
            expect(kdsHtml).toContain('F&B Container Café');
        });

        test('should have clock and date display', () => {
            expect(kdsHtml).toContain('id="kdsClock"');
            expect(kdsHtml).toContain('id="kdsDate"');
        });

        test('should have stats section', () => {
            expect(kdsHtml).toContain('class="kds-stats"');
        });

        test('should have pending stat item', () => {
            expect(kdsHtml).toContain('class="stat-item pending"');
            expect(kdsHtml).toContain('id="statPending"');
            expect(kdsHtml).toContain('Chờ');
        });

        test('should have preparing stat item', () => {
            expect(kdsHtml).toContain('class="stat-item preparing"');
            expect(kdsHtml).toContain('id="statPreparing"');
            expect(kdsHtml).toContain('Đang làm');
        });

        test('should have ready stat item', () => {
            expect(kdsHtml).toContain('class="stat-item ready"');
            expect(kdsHtml).toContain('id="statReady"');
            expect(kdsHtml).toContain('Sẵn sàng');
        });

        test('should have settings button', () => {
            expect(kdsHtml).toContain('class="kds-settings"');
            expect(kdsHtml).toContain('id="kdsSettings"');
            expect(kdsHtml).toContain('⚙️');
        });
    });

    describe('KDS Board - Order Columns', () => {
        test('should have main board container', () => {
            expect(kdsHtml).toContain('class="kds-board"');
        });

        test('should have pending column', () => {
            expect(kdsHtml).toContain('data-status="pending"');
            expect(kdsHtml).toContain('class="kds-column-header pending"');
            expect(kdsHtml).toContain('📋');
            expect(kdsHtml).toContain('Chờ Xử Lý');
            expect(kdsHtml).toContain('id="pendingCount"');
        });

        test('should have preparing column', () => {
            expect(kdsHtml).toContain('data-status="preparing"');
            expect(kdsHtml).toContain('class="kds-column-header preparing"');
            expect(kdsHtml).toContain('🔥');
            expect(kdsHtml).toContain('Đang Chế Biến');
            expect(kdsHtml).toContain('id="preparingCount"');
        });

        test('should have ready column', () => {
            expect(kdsHtml).toContain('data-status="ready"');
            expect(kdsHtml).toContain('class="kds-column-header ready"');
            expect(kdsHtml).toContain('✅');
            expect(kdsHtml).toContain('Sẵn Sàng');
            expect(kdsHtml).toContain('id="readyCount"');
        });

        test('should have completed column', () => {
            expect(kdsHtml).toContain('data-status="completed"');
            expect(kdsHtml).toContain('class="kds-column-header completed"');
            expect(kdsHtml).toContain('✔️');
            expect(kdsHtml).toContain('Hoàn Thành');
            expect(kdsHtml).toContain('id="completedCount"');
        });

        test('should have order containers for each column', () => {
            expect(kdsHtml).toContain('id="pendingOrders"');
            expect(kdsHtml).toContain('id="preparingOrders"');
            expect(kdsHtml).toContain('id="readyOrders"');
            expect(kdsHtml).toContain('id="completedOrders"');
        });
    });

    describe('New Order Alert System', () => {
        test('should have order alert container', () => {
            expect(kdsHtml).toContain('class="order-alert"');
            expect(kdsHtml).toContain('id="orderAlert"');
        });

        test('should have alert icon', () => {
            expect(kdsHtml).toContain('class="alert-icon"');
            expect(kdsHtml).toContain('🔔');
        });

        test('should have alert content with order ID', () => {
            expect(kdsHtml).toContain('class="alert-content"');
            expect(kdsHtml).toContain('Order Mới!');
            expect(kdsHtml).toContain('id="alertOrderId"');
        });

        test('should have dismiss button', () => {
            expect(kdsHtml).toContain('class="alert-dismiss"');
            expect(kdsHtml).toContain('id="alertDismiss"');
            expect(kdsHtml).toContain('✕');
        });
    });

    describe('Settings Modal', () => {
        test('should have settings modal', () => {
            expect(kdsHtml).toContain('id="kdsModal"');
            expect(kdsHtml).toContain('class="kds-modal"');
        });

        test('should have modal overlay', () => {
            expect(kdsHtml).toContain('class="kds-modal-overlay"');
        });

        test('should have modal header with title and close button', () => {
            expect(kdsHtml).toContain('class="kds-modal-header"');
            expect(kdsHtml).toContain('⚙️ Cài Đặt');
            expect(kdsHtml).toContain('id="kdsModalClose"');
        });

        test('should have sound toggle setting', () => {
            expect(kdsHtml).toContain('id="toggleSound"');
            expect(kdsHtml).toContain('Âm Thanh Thông Báo');
            expect(kdsHtml).toContain('class="toggle"');
        });

        test('should have auto refresh toggle setting', () => {
            expect(kdsHtml).toContain('id="toggleAutoRefresh"');
            expect(kdsHtml).toContain('Tự Động Làm Mới');
        });

        test('should have refresh interval input', () => {
            expect(kdsHtml).toContain('id="refreshInterval"');
            expect(kdsHtml).toContain('type="number"');
            expect(kdsHtml).toContain('value="5"');
            expect(kdsHtml).toContain('min="3"');
            expect(kdsHtml).toContain('max="60"');
        });

        test('should have view all orders button', () => {
            expect(kdsHtml).toContain('id="btnViewAllOrders"');
            expect(kdsHtml).toContain('📊 Xem Orders');
        });

        test('should have test order generator button', () => {
            expect(kdsHtml).toContain('id="btnGenerateTestOrder"');
            expect(kdsHtml).toContain('🧪 Tạo Order Test');
        });
    });

    describe('Order Detail Modal', () => {
        test('should have order detail modal', () => {
            expect(kdsHtml).toContain('id="orderDetailModal"');
            expect(kdsHtml).toContain('class="order-detail-modal"');
        });

        test('should have order detail title', () => {
            expect(kdsHtml).toContain('id="orderDetailTitle"');
            expect(kdsHtml).toContain('Order #--');
        });

        test('should have order detail close button', () => {
            expect(kdsHtml).toContain('id="orderDetailClose"');
        });

        test('should have order detail body container', () => {
            expect(kdsHtml).toContain('id="orderDetailBody"');
        });
    });

    describe('KDS JavaScript - State Management', () => {
        test('should have KDS_STATE object', () => {
            expect(kdsOrdersJs).toContain('const KDS_STATE');
            expect(kdsOrdersJs).toContain('orders: []');
            expect(kdsOrdersJs).toContain('settings:');
            expect(kdsOrdersJs).toContain('stats:');
        });

        test('should have settings configuration', () => {
            expect(kdsOrdersJs).toContain('soundEnabled:');
            expect(kdsOrdersJs).toContain('autoRefresh:');
            expect(kdsOrdersJs).toContain('refreshInterval:');
            expect(kdsOrdersJs).toContain('lastSync:');
        });

        test('should have stats tracking', () => {
            expect(kdsOrdersJs).toContain('pending:');
            expect(kdsOrdersJs).toContain('preparing:');
            expect(kdsOrdersJs).toContain('ready:');
            expect(kdsOrdersJs).toContain('completed:');
        });
    });

    describe('Menu Items Configuration', () => {
        test('should have MENU_ITEMS with drinks', () => {
            expect(kdsOrdersJs).toContain('const MENU_ITEMS');
            expect(kdsOrdersJs).toContain('drinks:');
            expect(kdsOrdersJs).toContain('Espresso');
            expect(kdsOrdersJs).toContain('Cappuccino');
            expect(kdsOrdersJs).toContain('Latte Art');
        });

        test('should have MENU_ITEMS with food', () => {
            expect(kdsOrdersJs).toContain('food:');
            expect(kdsOrdersJs).toContain('Croissant Bơ');
            expect(kdsOrdersJs).toContain('Bagel Sandwich');
            expect(kdsOrdersJs).toContain('Fries Giòn');
        });

        test('should have menu item properties', () => {
            expect(kdsOrdersJs).toContain('id:');
            expect(kdsOrdersJs).toContain('name:');
            expect(kdsOrdersJs).toContain('price:');
            expect(kdsOrdersJs).toContain('category:');
            expect(kdsOrdersJs).toContain('prepTime:');
        });
    });

    describe('Order Status Constants', () => {
        test('should have ORDER_STATUS enum', () => {
            expect(kdsOrdersJs).toContain('const ORDER_STATUS');
            expect(kdsOrdersJs).toContain('PENDING:');
            expect(kdsOrdersJs).toContain('PREPARING:');
            expect(kdsOrdersJs).toContain('READY:');
            expect(kdsOrdersJs).toContain('COMPLETED:');
        });
    });

    describe('Priority System', () => {
        test('should have PRIORITY enum', () => {
            expect(kdsOrdersJs).toContain('const PRIORITY');
            expect(kdsOrdersJs).toContain('RUSH:');
            expect(kdsOrdersJs).toContain('NORMAL:');
            expect(kdsOrdersJs).toContain('LOW:');
        });
    });

    describe('Order ID Generator', () => {
        test('should have generateOrderId function', () => {
            expect(kdsOrdersJs).toContain('function generateOrderId');
            expect(kdsOrdersJs).toContain('ORD-');
        });

        test('should have generateTableNumber function', () => {
            expect(kdsOrdersJs).toContain('function generateTableNumber');
        });

        test('should have generateRandomOrder function', () => {
            expect(kdsOrdersJs).toContain('function generateRandomOrder');
            expect(kdsOrdersJs).toContain('numDrinks');
            expect(kdsOrdersJs).toContain('numFood');
        });
    });

    describe('Local Storage Functions', () => {
        test('should have loadOrders function', () => {
            expect(kdsOrdersJs).toContain('function loadOrders');
            expect(kdsOrdersJs).toContain('localStorage.getItem');
            expect(kdsOrdersJs).toContain('kds_orders');
        });

        test('should have saveOrders function', () => {
            expect(kdsOrdersJs).toContain('function saveOrders');
            expect(kdsOrdersJs).toContain('localStorage.setItem');
        });

        test('should filter old completed orders', () => {
            expect(kdsOrdersJs).toContain('oneHourAgo');
            expect(kdsOrdersJs).toContain('3600000');
            expect(kdsOrdersJs).toContain('ORDER_STATUS.COMPLETED');
        });
    });

    describe('Order Status Transitions', () => {
        test('should have advanceOrderStatus function', () => {
            expect(kdsOrdersJs).toContain('function advanceOrderStatus');
            expect(kdsOrdersJs).toContain('transitions');
        });

        test('should have moveToPreviousStatus function', () => {
            expect(kdsOrdersJs).toContain('function moveToPreviousStatus');
        });

        test('should have proper status flow', () => {
            expect(kdsOrdersJs).toContain('[ORDER_STATUS.PENDING]: ORDER_STATUS.PREPARING');
            expect(kdsOrdersJs).toContain('[ORDER_STATUS.PREPARING]: ORDER_STATUS.READY');
            expect(kdsOrdersJs).toContain('[ORDER_STATUS.READY]: ORDER_STATUS.COMPLETED');
        });
    });

    describe('Format Utilities', () => {
        test('should have formatCurrency function', () => {
            expect(kdsOrdersJs).toContain('function formatCurrency');
            expect(kdsOrdersJs).toContain('Intl.NumberFormat');
            expect(kdsOrdersJs).toContain('vi-VN');
            expect(kdsOrdersJs).toContain('VND');
        });

        test('should have formatTime function', () => {
            expect(kdsOrdersJs).toContain('function formatTime');
            expect(kdsOrdersJs).toContain('hour:');
            expect(kdsOrdersJs).toContain('minute:');
        });

        test('should have formatDuration function', () => {
            expect(kdsOrdersJs).toContain('function formatDuration');
            expect(kdsOrdersJs).toContain('minutes');
            expect(kdsOrdersJs).toContain('seconds');
        });

        test('should have getPriorityClass function', () => {
            expect(kdsOrdersJs).toContain('function getPriorityClass');
            expect(kdsOrdersJs).toContain('priority-rush');
            expect(kdsOrdersJs).toContain('priority-low');
        });

        test('should have getPriorityLabel function', () => {
            expect(kdsOrdersJs).toContain('function getPriorityLabel');
            expect(kdsOrdersJs).toContain('🔥 GẤP');
            expect(kdsOrdersJs).toContain('⏱️ Từ từ');
        });
    });

    describe('Order Card Rendering', () => {
        test('should have renderOrderCard function', () => {
            expect(kdsOrdersJs).toContain('function renderOrderCard');
            expect(kdsOrdersJs).toContain('order-card');
        });

        test('should render order header with ID and priority', () => {
            expect(kdsOrdersJs).toContain('order-card-header');
            expect(kdsOrdersJs).toContain('order-number');
            expect(kdsOrdersJs).toContain('priority-badge');
        });

        test('should render order items', () => {
            expect(kdsOrdersJs).toContain('order-items');
            expect(kdsOrdersJs).toContain('item-qty');
            expect(kdsOrdersJs).toContain('item-name');
            expect(kdsOrdersJs).toContain('item-price');
        });

        test('should render order footer with total and timer', () => {
            expect(kdsOrdersJs).toContain('order-card-footer');
            expect(kdsOrdersJs).toContain('order-total');
            expect(kdsOrdersJs).toContain('order-timer');
        });

        test('should have order action buttons', () => {
            expect(kdsOrdersJs).toContain('order-actions');
            expect(kdsOrdersJs).toContain('btn-back');
            expect(kdsOrdersJs).toContain('btn-advance');
        });

        test('should handle dine-in and takeaway order types', () => {
            expect(kdsOrdersJs).toContain('dine-in');
            expect(kdsOrdersJs).toContain('takeaway');
            expect(kdsOrdersJs).toContain('tableNumber');
        });
    });

    describe('Render All Orders', () => {
        test('should have renderAllOrders function', () => {
            expect(kdsOrdersJs).toContain('function renderAllOrders');
        });

        test('should get all column containers', () => {
            expect(kdsOrdersJs).toContain('getElementById');
            expect(kdsOrdersJs).toContain('pendingOrders');
            expect(kdsOrdersJs).toContain('preparingOrders');
            expect(kdsOrdersJs).toContain('readyOrders');
            expect(kdsOrdersJs).toContain('completedOrders');
        });

        test('should filter orders by status', () => {
            expect(kdsOrdersJs).toContain('.filter(o => o.status === ORDER_STATUS.PENDING)');
            expect(kdsOrdersJs).toContain('.filter(o => o.status === ORDER_STATUS.PREPARING)');
            expect(kdsOrdersJs).toContain('.filter(o => o.status === ORDER_STATUS.READY)');
        });

        test('should have empty state fallback', () => {
            expect(kdsOrdersJs).toContain('empty-state');
            expect(kdsOrdersJs).toContain('Không có order');
        });
    });

    describe('Stats Update', () => {
        test('should have updateStats function', () => {
            expect(kdsOrdersJs).toContain('function updateStats');
        });

        test('should update stat DOM elements', () => {
            expect(kdsOrdersJs).toContain('getElementById');
            expect(kdsOrdersJs).toContain('statPending');
            expect(kdsOrdersJs).toContain('statPreparing');
            expect(kdsOrdersJs).toContain('statReady');
        });
    });

    describe('Clock System', () => {
        test('should have updateClock function', () => {
            expect(kdsOrdersJs).toContain('function updateClock');
        });

        test('should update clock and date elements', () => {
            expect(kdsOrdersJs).toContain('kdsClock');
            expect(kdsOrdersJs).toContain('kdsDate');
        });

        test('should use Vietnamese locale for time', () => {
            expect(kdsOrdersJs).toContain('vi-VN');
            expect(kdsOrdersJs).toContain('toLocaleTimeString');
            expect(kdsOrdersJs).toContain('toLocaleDateString');
        });

        test('should have interval timer for clock', () => {
            expect(kdsOrdersJs).toContain('setInterval(updateClock, 1000)');
        });
    });

    describe('Timer System', () => {
        test('should have updateTimers function', () => {
            expect(kdsOrdersJs).toContain('function updateTimers');
        });

        test('should update order timers', () => {
            expect(kdsOrdersJs).toContain('.order-timer');
            expect(kdsOrdersJs).toContain('elapsed');
            expect(kdsOrdersJs).toContain('formatDuration');
        });

        test('should handle overdue orders', () => {
            expect(kdsOrdersJs).toContain('order-overdue');
            expect(kdsOrdersJs).toContain('timer-danger');
            expect(kdsOrdersJs).toContain('minutes > 10');
        });
    });

    describe('New Order Alert System', () => {
        test('should have checkNewOrders function', () => {
            expect(kdsOrdersJs).toContain('function checkNewOrders');
            expect(kdsOrdersJs).toContain('lastOrderCount');
        });

        test('should have showAlert function', () => {
            expect(kdsOrdersJs).toContain('function showAlert');
            expect(kdsOrdersJs).toContain('orderAlert');
            expect(kdsOrdersJs).toContain('classList.add');
        });

        test('should have playNotificationSound function', () => {
            expect(kdsOrdersJs).toContain('function playNotificationSound');
            expect(kdsOrdersJs).toContain('AudioContext');
            expect(kdsOrdersJs).toContain('oscillator');
        });

        test('should use Web Audio API for beep', () => {
            expect(kdsOrdersJs).toContain('createOscillator');
            expect(kdsOrdersJs).toContain('gainNode');
            expect(kdsOrdersJs).toContain('frequency.value = 800');
        });
    });

    describe('Settings Modal Functions', () => {
        test('should have openSettingsModal function', () => {
            expect(kdsOrdersJs).toContain('function openSettingsModal');
        });

        test('should have closeSettingsModal function', () => {
            expect(kdsOrdersJs).toContain('function closeSettingsModal');
        });

        test('should have closeOrderDetailModal function', () => {
            expect(kdsOrdersJs).toContain('function closeOrderDetailModal');
        });

        test('should have initSettings function', () => {
            expect(kdsOrdersJs).toContain('function initSettings');
        });

        test('should have toggle sound handler', () => {
            expect(kdsOrdersJs).toContain('toggleSound');
            expect(kdsOrdersJs).toContain('soundEnabled');
        });

        test('should have toggle auto refresh handler', () => {
            expect(kdsOrdersJs).toContain('toggleAutoRefresh');
            expect(kdsOrdersJs).toContain('autoRefresh');
        });

        test('should have refresh interval input handler', () => {
            expect(kdsOrdersJs).toContain('refreshInterval');
            expect(kdsOrdersJs).toContain('Math.max(3000');
            expect(kdsOrdersJs).toContain('Math.min(60000');
        });
    });

    describe('Test Order Generator', () => {
        test('should have test order button handler', () => {
            expect(kdsOrdersJs).toContain('btnGenerateTest');
            expect(kdsOrdersJs).toContain('generateRandomOrder');
            expect(kdsOrdersJs).toContain('KDS_STATE.orders.push');
        });

        test('should have view all orders button handler', () => {
            expect(kdsOrdersJs).toContain('btnViewAll');
            expect(kdsOrdersJs).toContain('KDS_STATE.orders.map');
        });
    });

    describe('KDS Initialization', () => {
        test('should have initKDS function', () => {
            expect(kdsOrdersJs).toContain('function initKDS');
        });

        test('should load orders on init', () => {
            expect(kdsOrdersJs).toContain('loadOrders');
            expect(kdsOrdersJs).toContain('renderAllOrders');
            expect(kdsOrdersJs).toContain('updateStats');
        });

        test('should have auto-refresh interval', () => {
            expect(kdsOrdersJs).toContain('setInterval');
            expect(kdsOrdersJs).toContain('settings.refreshInterval');
            expect(kdsOrdersJs).toContain('Math.random() > 0.7');
        });

        test('should have timer update interval', () => {
            expect(kdsOrdersJs).toContain('setInterval(updateTimers, 1000)');
        });

        test('should attach modal event listeners', () => {
            expect(kdsOrdersJs).toContain('kdsSettings');
            expect(kdsOrdersJs).toContain('addEventListener');
            expect(kdsOrdersJs).toContain('kdsModalClose');
        });

        test('should have overlay click handler', () => {
            expect(kdsOrdersJs).toContain('.kds-modal-overlay');
            expect(kdsOrdersJs).toContain('classList.remove');
        });

        test('should start on DOMContentLoaded', () => {
            expect(kdsOrdersJs).toContain('DOMContentLoaded');
            expect(kdsOrdersJs).toContain('initKDS');
        });
    });

    describe('Global Function Exports', () => {
        test('should export advanceOrderStatus to window', () => {
            expect(kdsOrdersJs).toContain('window.advanceOrderStatus');
        });

        test('should export moveToPreviousStatus to window', () => {
            expect(kdsOrdersJs).toContain('window.moveToPreviousStatus');
        });
    });

    describe('CSS Integration', () => {
        test('should link to styles.css or minified version', () => {
            expect(kdsHtml).toMatch(/href=["'].*css[\"']/);
        });

        test('should have KDS specific classes in HTML', () => {
            expect(kdsHtml).toMatch(/kds-[a-z-]+/g);
        });
    });

    describe('File Size Checks', () => {
        test('HTML file should be under 50KB', () => {
            const sizeKb = Buffer.byteLength(kdsHtml, 'utf8') / 1024;
            expect(sizeKb).toBeLessThan(50);
        });

        test('JS file should be under 30KB', () => {
            const sizeKb = Buffer.byteLength(kdsOrdersJs, 'utf8') / 1024;
            expect(sizeKb).toBeLessThan(30);
        });
    });

    describe('Code Quality', () => {
        test('should not have TODO comments', () => {
            const todos = kdsOrdersJs.match(/TODO|FIXME/g) || [];
            expect(todos.length).toBe(0);
        });

        test('should use const/let instead of var', () => {
            const varDeclarations = kdsOrdersJs.match(/\bvar\b/g) || [];
            expect(varDeclarations.length).toBe(0);
        });
    });
});

describe('KDS Integration', () => {
    let kdsHtml;
    let kdsOrdersJs;
    let stylesCss;

    beforeAll(() => {
        kdsHtml = fs.readFileSync(path.join(__dirname, '../kitchen-display.html'), 'utf8');
        kdsOrdersJs = fs.readFileSync(path.join(__dirname, '../js/kds-app.js'), 'utf8');
        stylesCss = fs.readFileSync(path.join(__dirname, '../css/main.css'), 'utf8');
    });

    test('should link to kds-app.js or minified version', () => {
        expect(kdsHtml).toMatch(/src="kds-app(\.min)?\.js"/);
    });

    test('should have KDS styles in styles.css', () => {
        expect(stylesCss).toContain('.kds-');
    });

    test('should have order card styles', () => {
        expect(stylesCss).toContain('.order-card');
    });

    test('should have modal styles', () => {
        expect(stylesCss).toContain('.kds-modal');
        expect(stylesCss).toContain('.kds-modal-overlay');
    });

    test('should have responsive styles for KDS', () => {
        expect(stylesCss).toMatch(/@media.*max-width/s);
    });
});
