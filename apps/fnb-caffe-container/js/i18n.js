/**
 * i18n - Internationalization Module
 * Hỗ trợ đa ngôn ngữ VI/EN cho F&B Container Café
 */

// Dictionary ngôn ngữ
const translations = {
  vi: {
    // Navigation
    'nav.home': 'Trang Chủ',
    'nav.menu': 'Menu',
    'nav.loyalty': 'Loyalty',
    'nav.contact': 'Liên Hệ',
    'nav.order': '📞 Đặt Bàn',

    // Hero Section
    'hero.title': 'F&B Container Café',
    'hero.tagline': 'Where Flavor Meets Design',
    'hero.cta.primary': '🛒 Đặt Hàng Ngay',
    'hero.cta.secondary': '📍 Xem Vị Trí',
    'hero.hours': 'Mở cửa 7:00 - 22:00 hàng ngày',

    // Menu
    'menu.coffee': 'Cà Phê',
    'menu.tea': 'Trà',
    'menu.signature': 'Signature',
    'menu.snacks': 'Ăn Vặt',
    'menu.combo': 'Combo',

    // Order
    'order.cart': 'Giỏ Hàng',
    'order.total': 'Tổng Cộng',
    'order.payment': 'Thanh Toán',

    // Contact
    'contact.name': 'Họ Tên',
    'contact.phone': 'Số Điện Thoại',
    'contact.email': 'Email',
    'contact.message': 'Lời Nhắn',
    'contact.submit': 'Gửi Liên Hệ',

    // Language Toggle
    'lang.switch': 'Chuyển Ngôn Ngữ',

    // Features
    'feature.specialty': 'Specialty Coffee',
    'feature.specialty.desc': 'Cà phê chất lượng cao từ những vùng trồng cà phê tốt nhất',
    'feature.rooftop': 'Rooftop Bar',
    'feature.rooftop.desc': 'View đồng lúa panorama 360 độ giữa lòng Sa Đéc',
    'feature.cyberpunk': 'Cyberpunk Space',
    'feature.cyberpunk.desc': 'Không gian container 3 tầng độc đáo, check-in cực chất',
    'feature.container': 'Container Design',
    'feature.container.desc': 'Kiến trúc container công nghiệp độc đáo',

    // Menu Categories
    'menu.category.all': 'Tất Cả',
    'menu.category.coffee': 'Cà Phê',
    'menu.category.tea': 'Trà',
    'menu.category.specialty': 'Signature Drinks',
    'menu.category.snacks': 'Ăn Vặt',

    // Product
    'product.view_details': 'Xem Chi Tiết',
    'product.add_to_cart': 'Thêm Vào Giỏ',

    // Loyalty
    'loyalty.title': 'F&B Loyalty Club',
    'loyalty.tagline': 'Tích điểm đổi quà - Đặc quyền đẳng cấp',
    'loyalty.tier.bronze': 'Hạng Đồng',
    'loyalty.tier.silver': 'Hạng Bạc',
    'loyalty.tier.gold': 'Hạng Vàng',
    'loyalty.tier.diamond': 'Hạng Kim Cương',
    'loyalty.points': 'Điểm',
    'loyalty.rewards': 'Đổi Thưởng',
    'loyalty.history': 'Lịch Sử',

    // Checkout
    'checkout.title': 'Thanh Toán',
    'checkout.cart': 'Giỏ Hàng',
    'checkout.total': 'Tổng Cộng',
    'checkout.payment': 'Phương Thức Thanh Toán',
    'checkout.confirm': 'Xác Nhận Đơn Hàng',

    // Footer
    'footer.brand': 'F&B CONTAINER',
    'footer.tagline': 'Where Flavor Meets Design',
    'footer.links': 'Liên Kết',
    'footer.contact': 'Liên Hệ',
    'footer.social': 'Theo Dõi',
    'footer.address': '📍 Sa Đéc, Đồng Tháp',
    'footer.phone': '📞 0901 234 567',
    'footer.email': '✉️ hello@fnbcontainer.vn',
    'footer.copyright': '© 2026 F&B Container Café. Made with ❤️ in Sa Đéc.',

    // Common
    'common.loading': 'Đang tải...',
    'common.error': 'Có lỗi xảy ra',
    'common.success': 'Thành công',
    'common.close': 'Đóng',
    'common.cancel': 'Hủy',
    'common.confirm': 'Xác nhận',
    'common.save': 'Lưu',
    'common.delete': 'Xóa',
    'common.edit': 'Sửa',
    'common.search': 'Tìm kiếm',
    'common.filter': 'Bộ lọc',
    'common.sort': 'Sắp xếp',

    // Accessibility
    'a11y.menu': 'Menu điều hướng',
    'a11y.skip': 'Bỏ qua nội dung chính',
    'a11y.toggle_theme': 'Chuyển chế độ sáng/tối',
    'a11y.open_menu': 'Mở menu',
    'a11y.close_menu': 'Đóng menu',
    'a11y.cart': 'Giỏ hàng',
    'a11y.search': 'Tìm kiếm',

    // Order
    'order.status.pending': 'Chờ xử lý',
    'order.status.confirmed': 'Đã xác nhận',
    'order.status.preparing': 'Đang chế biến',
    'order.status.ready': 'Sẵn sàng',
    'order.status.delivered': 'Đã giao',
    'order.status.cancelled': 'Đã hủy',
    'order.number': 'Mã đơn hàng',
    'order.date': 'Ngày đặt',
    'order.items': 'Số lượng',
    'order.total': 'Tổng tiền',

    // Payment Methods
    'payment.cash': 'Tiền mặt',
    'payment.momo': 'MoMo',
    'payment.vnpay': 'VNPay',
    'payment.qr': 'QR Code',

    // Notifications
    'notify.added_to_cart': 'Đã thêm vào giỏ hàng',
    'notify.removed_from_cart': 'Đã xóa khỏi giỏ hàng',
    'notify.order_success': 'Đặt hàng thành công!',
    'notify.order_failed': 'Đặt hàng thất bại',
    'notify.login_required': 'Vui lòng đăng nhập',
    'notify.payment_success': 'Thanh toán thành công!',
    'notify.payment_failed': 'Thanh toán thất bại'
  },

  en: {
    // Navigation
    'nav.home': 'Home',
    'nav.menu': 'Menu',
    'nav.loyalty': 'Loyalty',
    'nav.contact': 'Contact',
    'nav.order': '📞 Book Table',

    // Hero Section
    'hero.title': 'F&B Container Café',
    'hero.tagline': 'Where Flavor Meets Design',
    'hero.cta.primary': '🛒 Order Now',
    'hero.cta.secondary': '📍 View Location',
    'hero.hours': 'Open 7:00 - 22:00 Daily',

    // Menu
    'menu.coffee': 'Coffee',
    'menu.tea': 'Tea',
    'menu.signature': 'Signature',
    'menu.snacks': 'Snacks',
    'menu.combo': 'Combo',

    // Order
    'order.cart': 'Cart',
    'order.total': 'Total',
    'order.payment': 'Payment',

    // Contact
    'contact.name': 'Full Name',
    'contact.phone': 'Phone Number',
    'contact.email': 'Email',
    'contact.message': 'Message',
    'contact.submit': 'Send Message',

    // Language Toggle
    'lang.switch': 'Switch Language',

    // Features
    'feature.specialty': 'Specialty Coffee',
    'feature.specialty.desc': 'Premium coffee from the finest coffee regions',
    'feature.rooftop': 'Rooftop Bar',
    'feature.rooftop.desc': '360° rice field panorama view in Sa Đéc',
    'feature.cyberpunk': 'Cyberpunk Space',
    'feature.cyberpunk.desc': 'Unique 3-floor container space, perfect for check-in',
    'feature.container': 'Container Design',
    'feature.container.desc': 'Unique industrial container architecture',

    // Menu Categories
    'menu.category.all': 'All',
    'menu.category.coffee': 'Coffee',
    'menu.category.tea': 'Tea',
    'menu.category.specialty': 'Signature Drinks',
    'menu.category.snacks': 'Snacks',

    // Product
    'product.view_details': 'View Details',
    'product.add_to_cart': 'Add to Cart',

    // Loyalty
    'loyalty.title': 'F&B Loyalty Club',
    'loyalty.tagline': 'Earn points, get rewards - Premium privileges',
    'loyalty.tier.bronze': 'Bronze Tier',
    'loyalty.tier.silver': 'Silver Tier',
    'loyalty.tier.gold': 'Gold Tier',
    'loyalty.tier.diamond': 'Diamond Tier',
    'loyalty.points': 'Points',
    'loyalty.rewards': 'Rewards',
    'loyalty.history': 'History',

    // Checkout
    'checkout.title': 'Checkout',
    'checkout.cart': 'Shopping Cart',
    'checkout.total': 'Total',
    'checkout.payment': 'Payment Method',
    'checkout.confirm': 'Confirm Order',

    // Footer
    'footer.brand': 'F&B CONTAINER',
    'footer.tagline': 'Where Flavor Meets Design',
    'footer.links': 'Links',
    'footer.contact': 'Contact',
    'footer.social': 'Follow Us',
    'footer.address': '📍 Sa Đéc, Đồng Tháp',
    'footer.phone': '📞 0901 234 567',
    'footer.email': '✉️ hello@fnbcontainer.vn',
    'footer.copyright': '© 2026 F&B Container Café. Made with ❤️ in Sa Đéc.',

    // Common
    'common.loading': 'Loading...',
    'common.error': 'An error occurred',
    'common.success': 'Success',
    'common.close': 'Close',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.save': 'Save',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.sort': 'Sort',

    // Accessibility
    'a11y.menu': 'Navigation menu',
    'a11y.skip': 'Skip to main content',
    'a11y.toggle_theme': 'Toggle light/dark mode',
    'a11y.open_menu': 'Open menu',
    'a11y.close_menu': 'Close menu',
    'a11y.cart': 'Shopping cart',
    'a11y.search': 'Search',

    // Order
    'order.status.pending': 'Pending',
    'order.status.confirmed': 'Confirmed',
    'order.status.preparing': 'Preparing',
    'order.status.ready': 'Ready',
    'order.status.delivered': 'Delivered',
    'order.status.cancelled': 'Cancelled',
    'order.number': 'Order Number',
    'order.date': 'Order Date',
    'order.items': 'Quantity',
    'order.total': 'Total Amount',

    // Payment Methods
    'payment.cash': 'Cash',
    'payment.momo': 'MoMo',
    'payment.vnpay': 'VNPay',
    'payment.qr': 'QR Code',

    // Notifications
    'notify.added_to_cart': 'Added to cart',
    'notify.removed_from_cart': 'Removed from cart',
    'notify.order_success': 'Order placed successfully!',
    'notify.order_failed': 'Order failed',
    'notify.login_required': 'Please log in',
    'notify.payment_success': 'Payment successful!',
    'notify.payment_failed': 'Payment failed'
  }
};

// Ngôn ngữ hiện tại
let _currentLang = 'vi';

/**
 * Lấy ngôn ngữ từ localStorage hoặc browser
 */
function getPreferredLanguage() {
  // Ưu tiên localStorage
  const saved = localStorage.getItem('language');
  if (saved && translations[saved]) {
    return saved;
  }

  // Fallback: browser language
  const browserLang = navigator.language?.split('-')[0] || 'vi';
  return translations[browserLang] ? browserLang : 'vi';
}

/**
 * Khởi tạo i18n
 */
function initI18n() {
  _currentLang = getPreferredLanguage();
  document.documentElement.lang = _currentLang;
  // Sync to window.I18N for test compatibility
  if (window.I18N) {
    window.I18N.currentLang = _currentLang;
  }
  applyTranslations();
  addLanguageToggle();
}

/**
 * Dịch một key
 * @param {string} key - Translation key
 * @param {object} params - Optional parameters
 * @returns {string} Translated text
 */
function t(key, params = {}) {
  // Check window.I18N.currentLang first (for test compatibility)
  const lang = (window.I18N && window.I18N.currentLang) || _currentLang;
  const translation = translations[lang]?.[key] || translations.vi[key] || key;

  // Replace parameters
  return Object.entries(params).reduce((str, [param, value]) => {
    return str.replace(new RegExp(`\\{${param}\\}`, 'g'), value);
  }, translation);
}

/**
 * Áp dụng translations cho tất cả elements có data-i18n attribute
 */
function applyTranslations() {
  const lang = (window.I18N && window.I18N.currentLang) || _currentLang;

  // Text content
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });

  // Placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(key);
  });

  // Title/aria-label
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    el.title = t(key);
  });

  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const key = el.getAttribute('data-i18n-aria');
    el.setAttribute('aria-label', t(key));
  });

  // Update lang attribute
  document.documentElement.lang = lang;

  // Emit event for custom handling
  window.dispatchEvent(new CustomEvent('i18n:updated', { detail: { lang } }));
}

/**
 * Chuyển ngôn ngữ
 * @param {string} lang - 'vi' hoặc 'en'
 */
function setLanguage(lang) {
  if (!translations[lang]) {
    return;
  }

  _currentLang = lang;
  // Sync to window.I18N for test compatibility
  if (window.I18N) {
    window.I18N.currentLang = lang;
  }
  localStorage.setItem('language', lang);
  translatePage();
}

/**
 * Toggle giữa VI và EN
 */
function toggleLanguage() {
  const newLang = ((window.I18N && window.I18N.currentLang) || _currentLang) === 'vi' ? 'en' : 'vi';
  setLanguage(newLang);
}

/**
 * Lấy ngôn ngữ hiện tại
 */
function getCurrentLang() {
  return (window.I18N && window.I18N.currentLang) || _currentLang;
}

/**
 * Lấy danh sách ngôn ngữ hỗ trợ
 */
function getSupportedLanguages() {
  return [
    { code: 'vi', name: 'Tiếng Việt', flag: '🇻🇳' },
    { code: 'en', name: 'English', flag: '🇬🇧' }
  ];
}

/**
 * Dịch toàn bộ trang
 */
function translatePage() {
  // Text content
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });

  // Placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(key);
  });

  // Title/aria-label
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    el.title = t(key);
  });

  document.querySelectorAll('[data-i18n-aria]').forEach(el => {
    const key = el.getAttribute('data-i18n-aria');
    el.setAttribute('aria-label', t(key));
  });

  // Update language toggle after translation
  updateLanguageToggle();
}

/**
 * Thêm language toggle button
 */
function addLanguageToggle() {
  // Don't create if already exists
  if (document.getElementById('langToggle')) {
    return;
  }

  const lang = (window.I18N && window.I18N.currentLang) || _currentLang;
  const toggle = document.createElement('button');
  toggle.id = 'langToggle';
  toggle.className = 'lang-toggle';
  toggle.setAttribute('aria-label', 'Switch language');
  toggle.innerHTML = `
    <span class="lang-icon">🌐</span>
    <span class="lang-text">${lang === 'vi' ? 'EN' : 'VI'}</span>
  `;

  toggle.addEventListener('click', () => {
    toggleLanguage();
  });

  // Add to nav
  const nav = document.querySelector('.nav-links');
  if (nav) {
    nav.appendChild(toggle);
  } else {
    document.body.appendChild(toggle);
  }
}

/**
 * Cập nhật language toggle text
 */
function updateLanguageToggle() {
  const toggle = document.getElementById('langToggle');
  if (!toggle) {
    return;
  }

  const lang = (window.I18N && window.I18N.currentLang) || _currentLang;
  const langText = toggle.querySelector('.lang-text');
  if (langText) {
    langText.textContent = lang === 'vi' ? 'EN' : 'VI';
  }
}

/**
 * Hiển thị toast notification
 */
function showToast(message) {
  // Remove existing toast if any
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }

  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #1a1612 0%, #2c2420 100%);
    color: #faf8f5;
    padding: 16px 24px;
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 9999;
    transition: transform 0.3s ease, opacity 0.3s ease;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(250, 248, 245, 0.1);
  `;

  document.body.appendChild(toast);

  // Auto remove after 4 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(-50%) translateY(100px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Export
const I18N = {
  init: initI18n,
  t,
  setLanguage,
  toggleLanguage,
  getCurrentLang,
  getSupportedLanguages,
  translations,
  translatePage,
  addLanguageToggle,
  updateLanguageToggle,
  showToast,
  defaultLang: 'vi',
  supportedLangs: ['vi', 'en'],
  get currentLang() {
    return _currentLang;
  },
  set currentLang(val) {
    _currentLang = val;
  }
};

window.i18n = I18N;

// CommonJS export for Jest tests
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { I18N };
}

// Auto-init khi DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initI18n);
} else {
  initI18n();
}
