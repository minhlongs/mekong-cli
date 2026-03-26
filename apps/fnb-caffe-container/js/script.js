/**
 * ═══════════════════════════════════════════════
 *  F&B CAFFE CONTAINER — Main Script (Orchestrator)
 *  Landing Page + Order System + Form Validation
 *  Imports modular components
 * ═══════════════════════════════════════════════
 */

// ─── Global Error Handlers ───

/**
 * Global uncaught error handler
 * Logs errors and shows user-friendly toast
 */
window.onerror = function(message, source, lineno, colno, error) {
  const errorInfo = {
    message: message,
    source: source,
    lineno: lineno,
    colno: colno,
    stack: error?.stack,
    timestamp: new Date().toISOString()
  };

  // Log to console for debugging
  console.error('[FNB Error]', errorInfo);

  // Send to error reporting service (if configured)
  if (typeof window.fnbErrorQueue === 'undefined') {
    window.fnbErrorQueue = [];
  }
  window.fnbErrorQueue.push(errorInfo);

  // Show user-friendly toast (don't expose technical details)
  if (typeof window.showToast === 'function') {
    const isNetworkError = message.toLowerCase().includes('network') ||
                          message.toLowerCase().includes('fetch') ||
                          message.toLowerCase().includes('offline');

    if (isNetworkError || !navigator.onLine) {
      window.showToast('⚠️ Mất kết nối. Vui lòng kiểm tra mạng và thử lại.', 'error');
    } else {
      window.showToast('⚠️ Có lỗi xảy ra. Vui lòng tải lại trang.', 'error');
    }
  }

  // Don't prevent default error handling
  return false;
};

/**
 * Global unhandled promise rejection handler
 */
window.onunhandledrejection = function(event) {
  const error = event.reason;
  const errorInfo = {
    message: error?.message || String(error),
    stack: error?.stack,
    timestamp: new Date().toISOString()
  };

  console.error('[FNB Unhandled Rejection]', errorInfo);

  // Queue for reporting
  if (typeof window.fnbErrorQueue === 'undefined') {
    window.fnbErrorQueue = [];
  }
  window.fnbErrorQueue.push(errorInfo);

  // Detect network errors
  const isNetworkError = errorInfo.message.toLowerCase().includes('network') ||
                        errorInfo.message.toLowerCase().includes('fetch') ||
                        errorInfo.message.toLowerCase().includes('timeout') ||
                        !navigator.onLine;

  if (typeof window.showToast === 'function') {
    if (isNetworkError) {
      window.showToast('⚠️ Mất kết nối. Vui lòng kiểm tra mạng và thử lại.', 'error');
    } else {
      window.showToast('⚠️ Có lỗi xảy ra. Vui lòng thử lại.', 'error');
    }
  }

  // Prevent console spam but allow default handling
  event.preventDefault();
};

// ─── Online/Offline Event Listeners ───

/**
 * Handle online/offline status changes
 */
window.addEventListener('offline', () => {
  console.warn('[FNB] App is offline');
  if (typeof window.showToast === 'function') {
    window.showToast('⚠️ Bạn đang offline. Một số tính năng có thể không khả dụng.', 'error');
  }
  document.body.classList.add('offline');
});

window.addEventListener('online', () => {
  console.log('[FNB] App is back online');
  if (typeof window.showToast === 'function') {
    window.showToast('✅ Đã kết nối lại thành công!', 'success');
  }
  document.body.classList.remove('offline');

  // Retry pending operations if any
  if (window.fnbRetryQueue && window.fnbRetryQueue.length > 0) {
    console.log(`[FNB] Retrying ${window.fnbRetryQueue.length} pending operations...`);
    window.fnbRetryQueue.forEach(fn => fn());
    window.fnbRetryQueue = [];
  }
});

// Import modules
import {
  initNavbar,
  initMobileMenu,
  initSmoothScroll,
  initThemeToggle,
  initGalleryLightbox,
  initMenuFilter
} from './navigation.js';

import { initHeroAnimations } from './hero.js';

import { initScrollReveal } from './scroll-effects.js';

import {
  initOrderSystem,
  initOrderModal,
  initContactForm,
  initCheckoutRedirect,
  registerServiceWorker,
  injectAnimationStyles,
  showToast
} from './order.js';

// Make showToast available globally for other modules
window.showToast = showToast;

// ─── Initialize All ───
document.addEventListener('DOMContentLoaded', () => {
  // Inject animation styles first
  injectAnimationStyles();

  // Hero & Scroll
  initHeroAnimations();
  initScrollReveal();

  // Navigation
  initNavbar();
  initMobileMenu();
  initSmoothScroll();
  initThemeToggle();

  // Order System
  initOrderModal();
  initOrderSystem();
  initContactForm();
  initCheckoutRedirect();

  // Menu & Gallery
  initMenuFilter();
  initGalleryLightbox();

  // Service Worker
  registerServiceWorker();
});
