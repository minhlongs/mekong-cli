/**
 * ═══════════════════════════════════════════════
 *  F&B CAFFE CONTAINER — Main Script (Orchestrator)
 *  Landing Page + Order System + Form Validation
 *  Imports modular components
 * ═══════════════════════════════════════════════
 */

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
