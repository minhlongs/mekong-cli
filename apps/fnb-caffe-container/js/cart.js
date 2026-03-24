/**
 * Cart Management Module
 * F&B Caffe Container - Shopping Cart Operations
 *
 * Handles: add/remove/update items, sync with API, localStorage fallback
 */

// Cart state
let cart = { items: [], total: 0, count: 0 };
let sessionId = null;
const API_BASE = 'http://localhost:8000/api';

/**
 * Initialize Session ID
 */
export function initSession() {
  sessionId = localStorage.getItem('fnb_session_id');
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('fnb_session_id', sessionId);
  }
  return sessionId;
}

/**
 * Get Session ID
 */
export function getSessionId() {
  return sessionId;
}

/**
 * Get API Base URL
 */
export function getApiBase() {
  return API_BASE;
}

/**
 * Load Cart from Backend API
 */
export async function loadCartFromAPI() {
  try {
    const response = await fetch(`${API_BASE}/cart?session_id=${sessionId}`);
    const result = await response.json();

    if (result.success) {
      cart = result.cart;
      return cart;
    } else {
      // Cart is empty
      cart = { items: [], total: 0, count: 0 };
      return cart;
    }
  } catch (error) {
    // Fallback to localStorage
    cart = JSON.parse(localStorage.getItem('cart')) || { items: [], total: 0, count: 0 };
    return cart;
  }
}

/**
 * Save Cart to LocalStorage
 */
export function saveCartToLocalStorage() {
  localStorage.setItem('cart', JSON.stringify(cart));
}

/**
 * Get Cart
 */
export function getCart() {
  return cart;
}

/**
 * Set Cart (for external sync)
 */
export function setCart(newCart) {
  cart = newCart;
  saveCartToLocalStorage();
}

/**
 * Update Cart Count (dispatch event)
 */
export function updateCartCount() {
  const count = cart.items ? cart.items.reduce((sum, item) => sum + item.quantity, 0) : 0;
  window.dispatchEvent(new CustomEvent('cartUpdated', { detail: { count } }));
  return count;
}

/**
 * Clear Cart
 */
export async function clearCart() {
  try {
    await fetch(`${API_BASE}/cart/clear?session_id=${sessionId}`, { method: 'POST' });
  } catch (error) {
    // Silent fail
  }
  localStorage.removeItem('cart');
  cart = { items: [], total: 0, count: 0 };
  updateCartCount();
  return cart;
}

/**
 * Remove Item from Cart
 */
export async function removeItem(id) {
  try {
    const response = await fetch(`${API_BASE}/cart/remove?item_id=${id}&session_id=${sessionId}`, {
      method: 'POST'
    });
    const result = await response.json();

    if (result.success) {
      cart = result.cart;
      saveCartToLocalStorage();
      updateCartCount();
      return { success: true, cart };
    } else {
      return { success: false, error: 'Không thể xóa sản phẩm' };
    }
  } catch (error) {
    // Fallback to localStorage
    cart.items = cart.items.filter(item => item.id !== id);
    saveCartToLocalStorage();
    updateCartCount();
    return { success: true, cart };
  }
}

/**
 * Check if Cart is Empty
 */
export function isCartEmpty() {
  return !cart.items || cart.items.length === 0;
}

/**
 * Get Cart Total
 */
export function getCartTotal() {
  return cart.total || 0;
}

/**
 * Get Cart Items
 */
export function getCartItems() {
  return cart.items || [];
}

/**
 * Render Cart to Summary Container
 */
export function renderCartSummary(containerId, formatPriceFn) {
  const summaryContainer = document.getElementById(containerId);
  if (!summaryContainer) {return null;}

  const items = cart.items || [];

  if (items.length === 0) {
    summaryContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">🛒 Giỏ hàng trống</p>';
    return 'empty';
  }

  summaryContainer.innerHTML = items.map(item => `
    <div class="summary-item" data-id="${item.id}">
      <div class="summary-item-info">
        <div class="summary-item-name">${item.name}</div>
        <div class="summary-item-meta">
          <span class="summary-item-qty">x${item.quantity}</span>
          · ${formatPriceFn(item.price)}
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 12px;">
        <span class="summary-item-price">${formatPriceFn(item.price * item.quantity)}</span>
        <button class="summary-item-remove" onclick="window.cartActions.removeItem('${item.id}')">×</button>
      </div>
    </div>
  `).join('');

  return 'loaded';
}

/**
 * Show Toast Notification
 */
export function showToast(message, type = 'info') {
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {existingToast.remove();}

  const toast = document.createElement('div');
  toast.className = `toast-notification toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#3b82f6'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);

  return toast;
}

/**
 * Handle Empty Cart
 */
export function handleEmptyCart(redirectUrl = 'menu.html') {
  const summaryContainer = document.getElementById('orderSummary');
  if (summaryContainer) {
    summaryContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">🛒 Giỏ hàng trống</p>';
  }

  if (confirm('🛒 Giỏ hàng trống. Chuyển đến menu để đặt hàng?')) {
    window.location.href = redirectUrl;
  }
}

// Export for global access (legacy compatibility)
window.cartManager = {
  getCart,
  setCart,
  loadCartFromAPI,
  clearCart,
  removeItem,
  updateCartCount,
  isCartEmpty,
  getCartTotal,
  getSessionId,
  renderCartSummary,
  showToast,
  handleEmptyCart,
};
