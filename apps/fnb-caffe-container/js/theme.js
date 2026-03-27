/**
 * Theme Manager — Dark/Light Mode Toggle
 * F&B CAFFE CONTAINER Design System
 *
 * Features:
 * - localStorage persistence
 * - System preference detection
 * - Instant theme application (prevents FOUC)
 * - Accessible toggle button
 */

export class ThemeManager {
  constructor() {
    this.theme = this.getInitialTheme();
    this.init();
  }

  /**
   * Get initial theme: localStorage → system preference → default (light)
   */
  getInitialTheme() {
    const stored = localStorage.getItem('theme');
    if (stored) {
      return stored;
    }
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  init() {
    // Apply theme immediately to prevent FOUC
    this.applyTheme();
    // Bind events after DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.bindEvents());
    } else {
      this.bindEvents();
    }
    // Listen for system theme changes
    this.listenToSystemChanges();
  }

  applyTheme() {
    document.documentElement.setAttribute('data-theme', this.theme);
    document.documentElement.style.colorScheme = this.theme;
    this.updateIcon();
    this.updateAriaLabel();
  }

  updateIcon() {
    const toggle = document.getElementById('themeToggle') || document.getElementById('theme-toggle');
    if (!toggle) return;

    const icon = toggle.querySelector('.theme-icon, .material-symbols-outlined, [aria-hidden="true"]');
    if (icon) {
      // Use emoji icons: 🌙 for dark mode (click to switch to light), 🌞 for light mode
      icon.textContent = this.theme === 'dark' ? '🌙' : '🌞';
    }
  }

  updateAriaLabel() {
    const toggle = document.getElementById('themeToggle') || document.getElementById('theme-toggle');
    if (!toggle) return;

    const nextTheme = this.theme === 'dark' ? 'light' : 'dark';
    toggle.setAttribute('aria-label', `Chuyển sang chế độ ${nextTheme}`);
  }

  toggle() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', this.theme);
    this.applyTheme();

    // Announce theme change for screen readers
    this.announceChange();
  }

  announceChange() {
    const announcement = document.getElementById('theme-announcement');
    if (announcement) {
      announcement.textContent = `Đã chuyển sang chế độ ${this.theme === 'dark' ? 'tối' : 'sáng'}`;
    } else {
      // Create announcement element if not exists
      const liveRegion = document.createElement('div');
      liveRegion.id = 'theme-announcement';
      liveRegion.setAttribute('role', 'status');
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.className = 'sr-only';
      liveRegion.textContent = `Đã chuyển sang chế độ ${this.theme === 'dark' ? 'tối' : 'sáng'}`;
      document.body.appendChild(liveRegion);
      setTimeout(() => liveRegion.remove(), 1000);
    }
  }

  bindEvents() {
    const themeToggle = document.getElementById('themeToggle') || document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggle();
      });

      // Keyboard support
      themeToggle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggle();
        }
      });
    }
  }

  listenToSystemChanges() {
    if (!window.matchMedia) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e) => {
      // Only update if user hasn't manually set a theme
      if (!localStorage.getItem('theme')) {
        this.theme = e.matches ? 'dark' : 'light';
        this.applyTheme();
      }
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
    } else if (mediaQuery.addListener) {
      // Legacy support
      mediaQuery.addListener(handler);
    }
  }

  /**
   * Get current theme
   */
  getTheme() {
    return this.theme;
  }

  /**
   * Set theme programmatically
   */
  setTheme(newTheme) {
    if (newTheme === 'dark' || newTheme === 'light') {
      this.theme = newTheme;
      localStorage.setItem('theme', newTheme);
      this.applyTheme();
    }
  }
}

// Initialize theme on page load (IIFE for immediate execution)
(function initTheme() {
  // Inline script to prevent FOUC - runs before render
  const stored = localStorage.getItem('theme');
  let theme = stored || 'light';

  // Check system preference if no stored preference
  if (!stored && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme = 'dark';
  }

  document.documentElement.setAttribute('data-theme', theme);
  document.documentElement.style.colorScheme = theme;

  // Export instance for external access
  window.themeManager = new ThemeManager();
})();
