/**
 * ═══════════════════════════════════════════════
 *  F&B CAFFE CONTAINER — API Client
 *  Centralized API client for all frontend modules
 * ═══════════════════════════════════════════════
 *
 * Provides unified interface for:
 * - Menu fetching
 * - Order management (create, read, update)
 * - Admin operations
 *
 * Features:
 * - Comprehensive error handling with try-catch
 * - Offline detection with navigator.onLine
 * - Custom error events for monitoring
 * - Request timeout with AbortController
 */

import { API_CONFIG } from './config.js';

// Debug logging configuration
const DEBUG = typeof FNB_DEBUG !== 'undefined' && FNB_DEBUG;

// ─── Error Types ───

/**
 * Custom error class for API errors
 */
export class APIError extends Error {
  constructor(message, statusCode, response) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.response = response;
    this.timestamp = new Date().toISOString();
  }
}

/**
 * Custom error class for network errors
 */
export class NetworkError extends Error {
  constructor(message) {
    super(message);
    this.name = 'NetworkError';
    this.timestamp = new Date().toISOString();
  }
}

/**
 * Custom error class for timeout errors
 */
export class TimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = 'TimeoutError';
    this.timestamp = new Date().toISOString();
  }
}

// ─── Offline Detection ───

/**
 * Check if app is currently offline
 * @returns {boolean} True if offline
 */
export function isOffline() {
  return !navigator.onLine;
}

/**
 * Throw error if offline
 * @throws {NetworkError} If offline
 */
export function checkOnlineStatus() {
  if (isOffline()) {
    throw new NetworkError('Network error: App is offline');
  }
}

// ─── Error Event Dispatcher ───

/**
 * Dispatch custom error event for monitoring
 * @param {string} type - Error type
 * @param {Error} error - Error object
 * @param {object} context - Additional context
 */
function dispatchErrorEvent(type, error, context = {}) {
  const event = new CustomEvent('fnb:error', {
    detail: {
      type,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      context,
      timestamp: new Date().toISOString()
    }
  });
  window.dispatchEvent(event);
  console.error(`[FNB API ${type}]`, error.message, context);
}

// ─── API Client Core ───
const apiClient = {
  /**
     * Generic GET request with error handling
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     * @returns {Promise<any>} Response data
     * @throws {NetworkError|TimeoutError|APIError}
     */
  async get(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE}${endpoint}`;

    // Check online status before making request
    checkOnlineStatus();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        dispatchErrorEvent('TIMEOUT', new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`), { endpoint, method: 'GET' });
      }, API_CONFIG.TIMEOUT);

      if (DEBUG) {console.log(`[FNB API GET] ${url}`);}

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        signal: controller.signal,
        ...options
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
        dispatchErrorEvent('HTTP_ERROR', error, { endpoint, status: response.status });
        throw error;
      }

      return await response.json();
    } catch (error) {
      // Handle abort/timeout
      if (error.name === 'AbortError') {
        const timeoutError = new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`);
        dispatchErrorEvent('TIMEOUT', timeoutError, { endpoint, method: 'GET' });
        throw timeoutError;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new NetworkError(`Network error: Unable to reach server (${endpoint})`);
        dispatchErrorEvent('NETWORK', networkError, { endpoint, method: 'GET' });
        throw networkError;
      }

      // Re-throw API errors (already dispatched)
      if (error instanceof APIError || error instanceof TimeoutError || error instanceof NetworkError) {
        throw error;
      }

      // Handle unknown errors
      dispatchErrorEvent('UNKNOWN', error, { endpoint, method: 'GET' });
      throw error;
    }
  },

  /**
     * Generic POST request with error handling
     * @param {string} endpoint - API endpoint
     * @param {object} data - Request body
     * @returns {Promise<any>} Response data
     * @throws {NetworkError|TimeoutError|APIError}
     */
  async post(endpoint, data = {}) {
    const url = `${API_CONFIG.BASE}${endpoint}`;

    // Check online status before making request
    checkOnlineStatus();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        dispatchErrorEvent('TIMEOUT', new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`), { endpoint, method: 'POST' });
      }, API_CONFIG.TIMEOUT);

      if (DEBUG) {console.log(`[FNB API POST] ${url}`, data);}

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
        dispatchErrorEvent('HTTP_ERROR', error, { endpoint, status: response.status, method: 'POST' });
        throw error;
      }

      return await response.json();
    } catch (error) {
      // Handle abort/timeout
      if (error.name === 'AbortError') {
        const timeoutError = new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`);
        dispatchErrorEvent('TIMEOUT', timeoutError, { endpoint, method: 'POST' });
        throw timeoutError;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new NetworkError(`Network error: Unable to reach server (${endpoint})`);
        dispatchErrorEvent('NETWORK', networkError, { endpoint, method: 'POST' });
        throw networkError;
      }

      // Re-throw API errors (already dispatched)
      if (error instanceof APIError || error instanceof TimeoutError || error instanceof NetworkError) {
        throw error;
      }

      // Handle unknown errors
      dispatchErrorEvent('UNKNOWN', error, { endpoint, method: 'POST' });
      throw error;
    }
  },

  /**
     * Generic PUT request with error handling
     * @param {string} endpoint - API endpoint
     * @param {object} data - Request body
     * @returns {Promise<any>} Response data
     * @throws {NetworkError|TimeoutError|APIError}
     */
  async put(endpoint, data = {}) {
    const url = `${API_CONFIG.BASE}${endpoint}`;

    // Check online status before making request
    checkOnlineStatus();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        dispatchErrorEvent('TIMEOUT', new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`), { endpoint, method: 'PUT' });
      }, API_CONFIG.TIMEOUT);

      if (DEBUG) {console.log(`[FNB API PUT] ${url}`, data);}

      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
        dispatchErrorEvent('HTTP_ERROR', error, { endpoint, status: response.status, method: 'PUT' });
        throw error;
      }

      return await response.json();
    } catch (error) {
      // Handle abort/timeout
      if (error.name === 'AbortError') {
        const timeoutError = new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`);
        dispatchErrorEvent('TIMEOUT', timeoutError, { endpoint, method: 'PUT' });
        throw timeoutError;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new NetworkError(`Network error: Unable to reach server (${endpoint})`);
        dispatchErrorEvent('NETWORK', networkError, { endpoint, method: 'PUT' });
        throw networkError;
      }

      // Re-throw API errors (already dispatched)
      if (error instanceof APIError || error instanceof TimeoutError || error instanceof NetworkError) {
        throw error;
      }

      // Handle unknown errors
      dispatchErrorEvent('UNKNOWN', error, { endpoint, method: 'PUT' });
      throw error;
    }
  },

  /**
     * Generic DELETE request with error handling
     * @param {string} endpoint - API endpoint
     * @param {object} options - Request options
     * @returns {Promise<any>} Response data
     * @throws {NetworkError|TimeoutError|APIError}
     */
  async delete(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE}${endpoint}`;

    // Check online status before making request
    checkOnlineStatus();

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        dispatchErrorEvent('TIMEOUT', new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`), { endpoint, method: 'DELETE' });
      }, API_CONFIG.TIMEOUT);

      if (DEBUG) {console.log(`[FNB API DELETE] ${url}`);}

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        signal: controller.signal,
        ...options
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error = new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
        dispatchErrorEvent('HTTP_ERROR', error, { endpoint, status: response.status, method: 'DELETE' });
        throw error;
      }

      return await response.json();
    } catch (error) {
      // Handle abort/timeout
      if (error.name === 'AbortError') {
        const timeoutError = new TimeoutError(`Request timeout after ${API_CONFIG.TIMEOUT}ms`);
        dispatchErrorEvent('TIMEOUT', timeoutError, { endpoint, method: 'DELETE' });
        throw timeoutError;
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const networkError = new NetworkError(`Network error: Unable to reach server (${endpoint})`);
        dispatchErrorEvent('NETWORK', networkError, { endpoint, method: 'DELETE' });
        throw networkError;
      }

      // Re-throw API errors (already dispatched)
      if (error instanceof APIError || error instanceof TimeoutError || error instanceof NetworkError) {
        throw error;
      }

      // Handle unknown errors
      dispatchErrorEvent('UNKNOWN', error, { endpoint, method: 'DELETE' });
      throw error;
    }
  }
};

// ─── Menu API ───

/**
 * Fetch full menu from API
 * @param {string} category - Optional category filter
 * @returns {Promise<Array>} Menu items
 */
export async function fetchMenu(category = null) {
  const endpoint = category
    ? `/menu?category=${encodeURIComponent(category)}`
    : '/menu';

  const result = await apiClient.get(endpoint);
  return result.data || result.menu || [];
}

/**
 * Fetch single menu item by ID
 * @param {number|string} itemId - Menu item ID
 * @returns {Promise<object>} Menu item
 */
export async function fetchMenuItem(itemId) {
  const result = await apiClient.get(`/menu/${itemId}`);
  return result.data || result.item || null;
}

// ─── Order API ───

/**
 * Create new order
 * @param {object} orderData - Order information
 * @param {Array} orderData.items - Order items
 * @param {string} orderData.fullName - Customer name
 * @param {string} orderData.phone - Customer phone
 * @param {string} orderData.address - Delivery address
 * @param {string} orderData.paymentMethod - Payment method
 * @param {number} orderData.total - Order total
 * @param {string} [orderData.notes] - Order notes
 * @returns {Promise<object>} Created order
 */
export async function createOrder(orderData) {
  const result = await apiClient.post('/orders', orderData);
  return result.data || result.order || result;
}

/**
 * Get order by ID
 * @param {string} orderId - Order ID
 * @returns {Promise<object>} Order details
 */
export async function getOrder(orderId) {
  const result = await apiClient.get(`/orders/${orderId}`);
  return result.data || result.order || null;
}

/**
 * Get orders by customer phone
 * @param {string} phone - Customer phone number
 * @returns {Promise<Array>} Customer orders
 */
export async function getOrderByPhone(phone) {
  const result = await apiClient.get(`/orders?phone=${encodeURIComponent(phone)}`);
  return result.data || result.orders || [];
}

/**
 * Update order status
 * @param {string} orderId - Order ID
 * @param {string} status - New status (pending, confirmed, preparing, ready, delivered, cancelled)
 * @param {string} [action] - Additional action (optional)
 * @returns {Promise<object>} Updated order
 */
export async function updateOrderStatus(orderId, status, action = 'update') {
  const result = await apiClient.put(`/orders/${orderId}/status`, {
    status,
    action
  });
  return result.data || result.order || result;
}

/**
 * Cancel order
 * @param {string} orderId - Order ID
 * @param {string} [reason] - Cancellation reason
 * @returns {Promise<object>} Updated order
 */
export async function cancelOrder(orderId, reason = '') {
  return updateOrderStatus(orderId, 'cancelled', reason);
}

// ─── Admin API ───

/**
 * Fetch all orders (admin)
 * @param {object} params - Query parameters
 * @param {string} [params.status] - Filter by status
 * @param {number} [params.limit] - Max results
 * @param {string} [params.sortBy] - Sort field
 * @param {string} [params.sortOrder] - Sort order (asc, desc)
 * @returns {Promise<Array>} Orders list
 */
export async function fetchAdminOrders(params = {}) {
  const queryString = new URLSearchParams(params).toString();
  const endpoint = queryString
    ? `/admin/orders?${queryString}`
    : '/admin/orders';

  const result = await apiClient.get(endpoint);
  return result.data || result.orders || [];
}

/**
 * Fetch dashboard statistics
 * @param {number} days - Number of days for stats
 * @returns {Promise<object>} Dashboard stats
 */
export async function fetchDashboardStats(days = 7) {
  const result = await apiClient.get(`/admin/stats?days=${days}`);
  return result.data || result.stats || null;
}

/**
 * Fetch revenue data
 * @param {number} days - Number of days
 * @returns {Promise<Array>} Revenue data
 */
export async function fetchRevenue(days = 7) {
  const result = await apiClient.get(`/admin/revenue?days=${days}`);
  return result.data || result.revenue || [];
}

/**
 * Fetch top products
 * @param {number} limit - Max products
 * @returns {Promise<Array>} Top products
 */
export async function fetchTopProducts(limit = 10) {
  const result = await apiClient.get(`/admin/products/top?limit=${limit}`);
  return result.data || result.products || [];
}

/**
 * Get order detail (admin)
 * @param {string} orderId - Order ID
 * @returns {Promise<object>} Order details
 */
export async function getAdminOrderDetail(orderId) {
  const result = await apiClient.get(`/admin/orders/${orderId}`);
  return result.data || result.order || null;
}

// ─── Payment API ───

/**
 * Create PayOS payment link
 * @param {object} paymentData - Payment info
 * @returns {Promise<string>} Checkout URL
 */
export async function createPayOSPayment(paymentData) {
  const result = await apiClient.post('/payment/payos', paymentData);
  return result.checkoutUrl || result.url || null;
}

/**
 * Create VNPay payment link
 * @param {object} paymentData - Payment info
 * @returns {Promise<string>} Payment URL
 */
export async function createVNPayPayment(paymentData) {
  const result = await apiClient.post('/payment/vnpay', paymentData);
  return result.paymentUrl || result.url || null;
}

/**
 * Create MoMo payment link
 * @param {object} paymentData - Payment info
 * @returns {Promise<string>} Payment URL
 */
export async function createMoMoPayment(paymentData) {
  const result = await apiClient.post('/payment/momo', paymentData);
  return result.payUrl || result.url || null;
}

// ─── Export API Client for custom use ───
export { apiClient };

// Default export
export default {
  fetchMenu,
  fetchMenuItem,
  createOrder,
  getOrder,
  getOrderByPhone,
  updateOrderStatus,
  cancelOrder,
  fetchAdminOrders,
  fetchDashboardStats,
  fetchRevenue,
  fetchTopProducts,
  getAdminOrderDetail,
  createPayOSPayment,
  createVNPayPayment,
  createMoMoPayment,
  apiClient
};
