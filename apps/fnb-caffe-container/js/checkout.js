/**
 * Checkout Orchestrator
 * F&B Caffe Container - Order Processing Coordinator
 *
 * This file coordinates between cart, payment, and validation modules
 * to handle the complete checkout flow.
 *
 * @module checkout
 */

// Import modules
import * as Cart from './cart.js';
import * as Payment from './payment.js';
import * as Validation from './validation.js';

// Config
const API_BASE = 'http://localhost:8000/api';
const DELIVERY_FEES = { default: 15000, far: 25000, freeThreshold: 300000 };
const FAR_WARDS = ['my-phuoc', 'tan-kien-dung', 'khac'];
const VALID_DISCOUNT_CODES = {
  'FIRSTORDER': { percent: 10, maxDiscount: 50000 },
  'WELCOME10': { percent: 10, maxDiscount: 30000 },
  'SADEC20': { percent: 20, maxDiscount: 100000 },
  'CONTAINER': { percent: 15, maxDiscount: 75000 }
};

// State
let discount = { code: null, percent: 0, amount: 0 };
let currentOrderForQR = null;
let orderWebSocket = null;
let sessionId = null;
let cart = { items: [], total: 0, count: 0 };

// Export for global access (legacy compatibility)
window.cartActions = { removeItem };

/**
 * Calculate Delivery Fee
 */
function calculateDeliveryFee(subtotal) {
  if (subtotal >= DELIVERY_FEES.freeThreshold) {return 0;}
  const ward = document.getElementById('ward')?.value;
  return FAR_WARDS.includes(ward) ? DELIVERY_FEES.far : DELIVERY_FEES.default;
}

/**
 * Update Totals Display
 */
function updateTotals(subtotal) {
  const deliveryFee = calculateDeliveryFee(subtotal);
  const discountAmount = discount.amount || 0;
  const total = subtotal + deliveryFee - discountAmount;

  const els = {
    subtotal: document.getElementById('summarySubtotal'),
    delivery: document.getElementById('summaryDelivery'),
    total: document.getElementById('summaryTotal'),
    btnTotal: document.getElementById('btnTotal'),
    discountRow: document.getElementById('discountRow'),
    discountCode: document.getElementById('discountCode'),
    summaryDiscount: document.getElementById('summaryDiscount')
  };

  if (els.subtotal) {els.subtotal.textContent = Payment.formatPrice(subtotal);}
  if (els.delivery) {els.delivery.textContent = deliveryFee === 0 ? 'Miễn phí' : Payment.formatPrice(deliveryFee);}
  if (els.total) {els.total.textContent = Payment.formatPrice(total);}
  if (els.btnTotal) {els.btnTotal.textContent = Payment.formatPrice(total);}

  if (discount.percent > 0 && els.discountRow) {
    els.discountRow.style.display = 'flex';
    if (els.discountCode) {els.discountCode.textContent = discount.code;}
    if (els.summaryDiscount) {els.summaryDiscount.textContent = `-${Payment.formatPrice(discountAmount)}`;}
  } else if (els.discountRow) {
    els.discountRow.style.display = 'none';
  }
}

/**
 * Load Cart to Summary
 */
function loadCartToSummary() {
  const summaryContainer = document.getElementById('orderSummary');
  if (!summaryContainer) {return;}

  const items = cart.items || [];
  if (items.length === 0) {
    Cart.handleEmptyCart();
    return;
  }

  summaryContainer.innerHTML = items.map(item => `
    <div class="summary-item" data-id="${item.id}">
      <div class="summary-item-info">
        <div class="summary-item-name">${Validation.escapeHtml(item.name)}</div>
        <div class="summary-item-meta">
          <span class="summary-item-qty">x${item.quantity}</span>
          · ${Payment.formatPrice(item.price)}
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 12px;">
        <span class="summary-item-price">${Payment.formatPrice(item.price * item.quantity)}</span>
        <button class="summary-item-remove" onclick="window.cartActions.removeItem('${item.id}')">×</button>
      </div>
    </div>
  `).join('');

  updateTotals(cart.total || 0);
}

/**
 * Remove Item from Cart
 */
async function removeItem(id) {
  if (!confirm('Xóa món này khỏi giỏ hàng?')) {return;}

  const result = await Cart.removeItem(id);
  if (result.success) {
    cart = result.cart;
    loadCartToSummary();
    Cart.showToast('Đã xóa sản phẩm', 'success');
  } else {
    Cart.showToast(result.error || 'Không thể xóa sản phẩm', 'error');
  }

  if (!cart.items || cart.items.length === 0) {
    setTimeout(() => {
      if (confirm('🛒 Giỏ hàng trống. Quay lại menu?')) {
        window.location.href = 'menu.html';
      }
    }, 500);
  }
}

/**
 * Initialize Delivery Time Toggle
 */
function initDeliveryTimeToggle() {
  const radioCards = document.querySelectorAll('input[name="deliveryTime"]');
  const scheduledTimeInput = document.getElementById('scheduledTime');

  radioCards.forEach(radio => {
    radio.addEventListener('change', () => {
      if (radio.value === 'scheduled') {
        scheduledTimeInput.classList.remove('hidden');
        scheduledTimeInput.required = true;
      } else {
        scheduledTimeInput.classList.add('hidden');
        scheduledTimeInput.required = false;
      }
    });
  });
}

/**
 * Initialize Payment Method Select
 */
function initPaymentMethodSelect() {
  document.querySelectorAll('.payment-card').forEach(card => {
    card.addEventListener('click', () => {
      const radio = card.querySelector('input[type="radio"]');
      radio.checked = true;
      document.querySelectorAll('.payment-card').forEach(c => c.classList.remove('selected'));
      card.classList.add('selected');
    });
  });
}

/**
 * Initialize Discount Code Handler
 */
function initDiscountCode() {
  const applyBtn = document.getElementById('applyDiscountBtn');
  const codeInput = document.getElementById('discountCode');
  if (!applyBtn) {return;}

  applyBtn.addEventListener('click', () => {
    const code = codeInput.value.trim().toUpperCase();
    if (!code) {
      alert('⚠️ Vui lòng nhập mã giảm giá');
      return;
    }

    if (VALID_DISCOUNT_CODES[code]) {
      const subtotal = cart.total || 0;
      let discountAmount = (subtotal * VALID_DISCOUNT_CODES[code].percent) / 100;
      if (VALID_DISCOUNT_CODES[code].maxDiscount && discountAmount > VALID_DISCOUNT_CODES[code].maxDiscount) {
        discountAmount = VALID_DISCOUNT_CODES[code].maxDiscount;
      }

      discount = { code, percent: VALID_DISCOUNT_CODES[code].percent, amount: discountAmount };
      alert(`✅ Áp dụng mã giảm giá thành công! Giảm ${VALID_DISCOUNT_CODES[code].percent}% (tối đa ${Payment.formatPrice(VALID_DISCOUNT_CODES[code].maxDiscount)})`);
      updateTotals(subtotal);
    } else {
      alert('❌ Mã giảm giá không hợp lệ');
      discount = { code: null, percent: 0, amount: 0 };
      updateTotals(cart.total || 0);
    }
  });
}

/**
 * Send Order to WebSocket
 */
function sendOrderToWebSocket(order) {
  if (!window.OrderTracker || !window.OrderTracker.ws) {return;}
  try {
    window.OrderTracker.sendNewOrder({
      id: order.id,
      customer: order.customer,
      items: order.items || [],
      total: order.total,
      payment_method: order.payment_method,
      status: 'pending',
      created_at: order.created_at || new Date().toISOString()
    });
  } catch (_) {}
}

/**
 * Send Order to Zalo
 */
function sendOrderToZalo(order) {
  const itemsText = order.items.map(item =>
    `• ${Validation.escapeHtml(item.name)} x${item.quantity} - ${Payment.formatPrice(item.price * item.quantity)}`
  ).join('\n');

  const zaloMessage = `
🛒 *ĐƠN HÀNG MỚI - F&B CONTAINER*
━━━━━━━━━━━━━━━━━━━━━━
📋 Mã đơn: ${order.id}
━━━━━━━━━━━━━━━━━━━━━━
👤 Khách hàng: ${Validation.escapeHtml(order.customer.full_name)}
📞 SĐT: ${Validation.escapeHtml(order.customer.phone)}
📍 Địa chỉ: ${Validation.escapeHtml(order.customer.address)}
⏰ Giao hàng: ${order.deliveryTime === 'now' ? '🚀 Ngay (15-20p)' : '📅 ' + order.scheduledTime}
━━━━━━━━━━━━━━━━━━━━━━
${itemsText}
━━━━━━━━━━━━━━━━━━━━━━
💰 Tạm tính: ${Payment.formatPrice(order.subtotal)}
🚛 Phí giao: ${Payment.formatPrice(order.shipping_fee)}
${order.discount > 0 ? `🏷️ Giảm giá: -${Payment.formatPrice(order.discount)}\n` : ''}
💵 *Tổng cộng: ${Payment.formatPrice(order.total)}*
💳 Thanh toán: ${Payment.translatePaymentMethod(order.payment_method)}
━━━━━━━━━━━━━━━━━━━━━━
  `.trim();

  window.open(`https://zalo.me/0901234567?text=${encodeURIComponent(zaloMessage)}`, '_blank');
}

/**
 * Show Success Modal
 */
function showSuccessModal(order) {
  const modal = document.getElementById('successModal');
  const orderDetails = document.getElementById('orderDetails');
  if (!modal || !orderDetails) {return;}

  orderDetails.innerHTML = `
    <h3>Thông tin đơn hàng</h3>
    <div class="order-details-row"><span>Mã đơn:</span><span>${Validation.escapeHtml(order.id)}</span></div>
    <div class="order-details-row"><span>Tổng cộng:</span><span>${Payment.formatPrice(order.total)}</span></div>
    <div class="order-details-row"><span>Thanh toán:</span><span>${Payment.translatePaymentMethod(order.payment_method)}</span></div>
  `;
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
}

/**
 * Handle COD Success
 */
async function handleCODSuccess(order) {
  await Cart.clearCart();
  showSuccessModal(order);
  sendOrderToZalo(order);
  sendOrderToWebSocket(order);
}

/**
 * Handle Payment Methods
 */
async function handlePayment(order, method) {
  const savePending = () => localStorage.setItem('pendingOrder', JSON.stringify(order));

  switch (method) {
  case 'cod':
    await handleCODSuccess(order);
    break;
  case 'momo':
  case 'vnpay': {
    try {
      const response = await fetch(`${API_BASE}/payment/create-url?order_id=${order.id}&payment_method=${method}&amount=${order.total}`);
      const result = await response.json();
      if (result.success && result.payment_url) {
        savePending();
        sendOrderToWebSocket(order);
        window.location.href = result.payment_url;
      } else {
        throw new Error('Không thể tạo liên kết thanh toán');
      }
    } catch (_) {
      window.paymentQR.handlePayment(order, method);
    }
    break;
  }
  case 'payos': {
    try {
      const response = await fetch(`${API_BASE}/payment/create-url?order_id=${order.id}&payment_method=${method}&amount=${order.total}`);
      const result = await response.json();
      if (result.success && result.payment_url) {
        savePending();
        sendOrderToWebSocket(order);
        window.location.href = result.payment_url;
      } else {
        throw new Error('Không thể tạo liên kết thanh toán PayOS');
      }
    } catch (_) {
      await handleCODSuccess(order);
    }
    break;
  }
  default:
    Cart.showToast('Phương thức thanh toán không hợp lệ', 'error');
  }
}

/**
 * Initialize Submit Order
 */
function initSubmitOrder() {
  const submitBtn = document.getElementById('submitOrderBtn');
  if (!submitBtn) {return;}

  submitBtn.addEventListener('click', async () => {
    const form = document.getElementById('checkoutForm');
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const items = cart.items || [];
    if (items.length === 0) {
      Cart.showToast('🛒 Giỏ hàng trống. Vui lòng chọn món!', 'error');
      return;
    }

    const formData = new FormData(form);
    const subtotal = cart.total || 0;
    const deliveryFee = calculateDeliveryFee(subtotal);
    const discountAmount = discount.amount || 0;
    const total = subtotal + deliveryFee - discountAmount;

    const orderData = {
      session_id: sessionId,
      customer: {
        full_name: formData.get('name'),
        phone: formData.get('phone'),
        email: formData.get('email'),
        address: formData.get('address'),
        ward: formData.get('ward'),
        district: 'Sa Đéc',
        city: 'Đồng Tháp',
        notes: formData.get('notes')
      },
      payment_method: document.querySelector('input[name="paymentMethod"]:checked')?.value
    };

    // Validate order data
    const validation = Validation.validateOrderData(orderData);
    if (!validation.valid) {
      Cart.showToast('⚠️ ' + validation.error, 'error');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-text">⏳ Đang xử lý...</span>';
    submitBtn.style.opacity = '0.7';

    try {
      const response = await fetch(`${API_BASE}/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      });

      const result = await response.json();
      if (result.success) {
        await handlePayment(result.order, result.order.payment_method);
      } else {
        throw new Error(result.detail || 'Có lỗi xảy ra');
      }
    } catch (error) {
      Cart.showToast('⚠️ Lỗi: ' + error.message, 'error');
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<span class="btn-text">✅ Xác Nhận Đặt Hàng</span>';
      submitBtn.style.opacity = '1';
    }
  });
}

/**
 * Initialize Theme Toggle
 */
function initThemeToggle() {
  const themeToggle = document.getElementById('themeToggle');
  const themeIcon = themeToggle?.querySelector('.theme-icon');
  if (!themeToggle) {return;}

  const savedTheme = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (themeIcon) {themeIcon.textContent = savedTheme === 'dark' ? '🌙' : '☀️';}

  themeToggle.addEventListener('click', () => {
    const newTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    if (themeIcon) {themeIcon.textContent = newTheme === 'dark' ? '🌙' : '☀️';}
  });
}

/**
 * Initialize WebSocket Tracking
 */
async function initializeWebSocketTracking() {
  if (!window.WebSocketClient) {return;}

  try {
    orderWebSocket = new window.WebSocketClient();
    const trackingOrderId = localStorage.getItem('trackingOrderId');

    orderWebSocket.on('connected', () => Cart.showToast('📡 Đã kết nối theo dõi đơn hàng', 'success'));
    orderWebSocket.on('new_order', (data) => {
      Cart.showToast('✅ Đơn hàng đã được tạo!', 'success');
      if (data.id) {localStorage.setItem('trackingOrderId', data.id);}
    });
    orderWebSocket.on('order_updated', (data) => {
      const statusLabels = {
        pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', preparing: 'Đang chế biến',
        ready: 'Sẵn sàng', delivered: 'Đã giao', cancelled: 'Đã hủy'
      };
      Cart.showToast(`📦 Đơn hàng: ${statusLabels[data.status] || data.status}`, 'info');
    });
    orderWebSocket.on('error', (data) => Cart.showToast('⚠️ Lỗi kết nối: ' + (data.message || 'Không xác định'), 'error'));

    await orderWebSocket.connect('customer', trackingOrderId);
    orderWebSocket.startHeartbeat(30000);
  } catch (_) {}
}

/**
 * Initialize Checkout
 */
async function initCheckout() {
  sessionId = Cart.initSession();
  cart = await Cart.loadCartFromAPI();
  if (Cart.isCartEmpty()) {
    Cart.handleEmptyCart();
  } else {
    loadCartToSummary();
  }
}

// DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initCheckout();
  initDeliveryTimeToggle();
  initPaymentMethodSelect();
  initDiscountCode();
  initSubmitOrder();
  initThemeToggle();
  initializeWebSocketTracking();
});

// Export for global access
window.checkoutUtils = { removeItem, formatPrice: Payment.formatPrice };
window.paymentQR = {
  open: (order, method = 'qr-bank') => {
    currentOrderForQR = order;
    const modal = document.getElementById('paymentQrModal');
    if (!modal) {return;}
    modal.style.display = 'flex';
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    // QR handling would be implemented here
  },
  close: () => {
    const modal = document.getElementById('paymentQrModal');
    if (modal) {
      modal.style.display = 'none';
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  },
  handlePayment: (order, method) => {
    localStorage.setItem('pendingOrder', JSON.stringify(order));
    sendOrderToWebSocket(order);
    const qrMethod = method === 'momo' ? 'momo-qr' : method === 'vnpay' ? 'vnpay-qr' : 'qr-bank';
    window.paymentQR.open(order, qrMethod);
  }
};
