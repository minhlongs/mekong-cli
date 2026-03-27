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
    'nav.about': 'Về Chúng Tôi',
    'nav.reservation': 'Đặt Bàn',

    // Hero Section
    'hero.title': 'F&B Container Café',
    'hero.title.line1': 'F&B',
    'hero.title.line2': 'CONTAINER',
    'hero.tagline': 'Where Flavor Meets Design',
    'hero.subtitle': 'Specialty Coffee × Rooftop Bar × Check-in Cyberpunk',
    'hero.cta.primary': '🛒 Đặt Hàng Ngay',
    'hero.cta.secondary': '📍 Xem Vị Trí',
    'hero.hours': 'Mở cửa 7:00 - 22:00 hàng ngày',
    'hero.badge': 'Mở Cửa Mỗi Ngày | 7:00 - 22:00',
    'hero.btn.order': '☕ Xem Menu',
    'hero.btn.location': '📍 Chỉ Đường',

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
    'lang.switch.to_en': '🌐 EN',
    'lang.switch.to_vi': '🌐 VI',

    // Features
    'feature.specialty': 'Specialty Coffee',
    'feature.specialty.desc': 'Cà phê chất lượng cao từ những vùng trồng cà phê tốt nhất',
    'feature.rooftop': 'Rooftop Bar',
    'feature.rooftop.desc': 'View đồng lúa panorama 360 độ giữa lòng Sa Đéc',
    'feature.cyberpunk': 'Cyberpunk Space',
    'feature.cyberpunk.desc': 'Không gian container 3 tầng độc đáo, check-in cực chất',
    'feature.container': 'Container Design',
    'feature.container.desc': 'Kiến trúc container công nghiệp độc đáo',

    // About Section
    'about.label': 'Câu Chuyện Của Chúng Tôi',
    'about.title': 'Từ Sa Đéc Với Yêu Thương',
    'about.desc': 'F&B Container Café được sinh ra từ tình yêu dành cho quê hương Sa Đéc. Chúng tôi mang đến không gian độc đáo với kiến trúc container industrial kết hợp với thiên nhiên rooftop, tạo nên điểm đến lý tưởng cho giới trẻ.',
    'about.highlight.1': '100% cà phê nguyên chất từ Buon Ma Thuot',
    'about.highlight.2': 'Rooftop bar view đồng lúa hoàng hôn',
    'about.highlight.3': 'Không gian check-in cyberpunk độc đáo',
    'about.btn.learn': 'Tìm Hiểu Thêm',

    // Menu Categories
    'menu.category.all': 'Tất Cả',
    'menu.category.coffee': 'Cà Phê',
    'menu.category.tea': 'Trà',
    'menu.category.specialty': 'Signature Drinks',
    'menu.category.snacks': 'Ăn Vặt',
    'menu.category.combo': 'Combo',

    // Product
    'product.view_details': 'Xem Chi Tiết',
    'product.add_to_cart': 'Thêm Vào Giỏ',

    // Order Modal
    'order.title': 'Đặt Hàng Online',
    'order.subtitle': 'Nhận hàng sau 15-20 phút',
    'order.tab.menu': 'Menu',
    'order.tab.cart': 'Giỏ Hàng',
    'order.cart.empty': 'Giỏ hàng trống',
    'order.cart.subtotal': 'Tạm tính',
    'order.cart.delivery': 'Phí giao hàng',
    'order.cart.total': 'Tổng cộng',
    'order.cart.checkout': '📦 Gửi Order Qua Zalo',
    'order.cart.items': 'món',
    'order.cart.remove': 'Xóa',
    'order.cart.quantity': 'Số lượng',
    'order.cart.note': 'Ghi chú (tùy chọn)',
    'order.cart.note.placeholder': 'Ví dụ: Ít đường, không đá...',

    // Order (expanded)
    'order.cart': 'Giỏ Hàng',
    'order.total': 'Tổng Cộng',
    'order.payment': 'Thanh Toán',

    // Payment Methods
    'payment.cash': 'Tiền mặt',
    'payment.momo': 'MoMo',
    'payment.vnpay': 'VNPay',
    'payment.qr': 'QR Code',

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
    'loyalty.welcome': 'Chào mừng đến với F&B Loyalty Club',
    'loyalty.earned': 'Đã tích lũy',
    'loyalty.next_tier': 'Điểm đến hạng tiếp theo',
    'loyalty.perks': 'Đặc quyền',
    'loyalty.join': 'Tham gia ngay',

    // Checkout
    'checkout.title': 'Thanh Toán',
    'checkout.cart': 'Giỏ Hàng',
    'checkout.total': 'Tổng Cộng',
    'checkout.payment': 'Phương Thức Thanh Toán',
    'checkout.confirm': 'Xác Nhận Đơn Hàng',
    'checkout.customer_info': 'Thông tin khách hàng',
    'checkout.delivery_address': 'Địa chỉ giao hàng',
    'checkout.delivery_method': 'Phương thức nhận hàng',
    'checkout.delivery_method.pickup': 'Nhận tại quán',
    'checkout.delivery_method.delivery': 'Giao hàng tận nơi',
    'checkout.order_summary': 'Tóm tắt đơn hàng',
    'checkout.place_order': 'Đặt hàng ngay',

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
    'footer.privacy': 'Chính sách bảo mật',
    'footer.terms': 'Điều khoản dịch vụ',

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
    'common.yes': 'Có',
    'common.no': 'Không',
    'common.ok': 'OK',
    'common.back': 'Quay lại',
    'common.next': 'Tiếp theo',
    'common.required': 'Bắt buộc',
    'common.optional': 'Tùy chọn',

    // Accessibility
    'a11y.menu': 'Menu điều hướng',
    'a11y.skip': 'Bỏ qua nội dung chính',
    'a11y.toggle_theme': 'Chuyển chế độ sáng/tối',
    'a11y.open_menu': 'Mở menu',
    'a11y.close_menu': 'Đóng menu',
    'a11y.cart': 'Giỏ hàng',
    'a11y.search': 'Tìm kiếm',
    'a11y.language': 'Chuyển ngôn ngữ',

    // Order Status
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
    'order.track': 'Theo dõi đơn hàng',
    'order.history': 'Lịch sử đơn hàng',
    'order.empty': 'Chưa có đơn hàng nào',
    'order.view_details': 'Xem chi tiết',

    // Contact Form
    'contact.name': 'Họ Tên',
    'contact.phone': 'Số Điện Thoại',
    'contact.email': 'Email',
    'contact.message': 'Lời Nhắn',
    'contact.submit': 'Gửi Liên Hệ',
    'contact.success': 'Cảm ơn bạn đã liên hệ!',
    'contact.error': 'Có lỗi xảy ra, vui lòng thử lại',
    'contact.label': 'Liên Hệ',
    'contact.title': 'Kết Nối Cùng Chúng Tôi',
    'contact.desc': 'Đặt bàn, tổ chức sự kiện, hay hợp tác kinh doanh. Chúng tôi phản hồi trong 24h.',
    'contact.form.name': 'Họ tên',
    'contact.form.name.placeholder': 'Nguyễn Văn A',
    'contact.form.phone': 'Số điện thoại',
    'contact.form.phone.placeholder': '0901234567',
    'contact.form.email': 'Email',
    'contact.form.email.placeholder': 'example@email.com',
    'contact.form.subject': 'Chủ đề',
    'contact.form.subject.select': '-- Chọn chủ đề --',
    'contact.form.subject.reservation': 'Đặt bàn',
    'contact.form.subject.event': 'Tổ chức sự kiện/sinh nhật',
    'contact.form.subject.meeting': 'Thuê meeting room',
    'contact.form.subject.partnership': 'Hợp tác kinh doanh',
    'contact.form.subject.feedback': 'Góp ý khác',
    'contact.form.message': 'Tin nhắn',
    'contact.form.message.placeholder': 'Nội dung tin nhắn...',
    'contact.form.submit': '📨 Gửi Tin Nhắn',

    // Rooftop Section
    'rooftop.label': 'Sunset Sessions',
    'rooftop.title': 'Chill Trên Mây',
    'rooftop.desc': 'Rooftop deck nhìn ra đồng lúa bát ngát và skyline Sa Đéc. String lights, ghế sofa, và specialty drinks — điểm đến lý tưởng cho hoàng hôn và after-work hangs.',
    'rooftop.highlight.view': 'View đồng lúa',
    'rooftop.highlight.lights': 'String lights',
    'rooftop.highlight.bar': 'Rooftop bar',
    'rooftop.highlight.wifi': 'WiFi全覆盖',

    // Location Section
    'location.label': 'Tìm Chúng Tôi',
    'location.title': 'Giữa Lòng Thành Phố Hoa',
    'location.address': '📍 Địa chỉ: 91 Hùng Vương, Phường Tân Phú Đông, Sa Đéc, Đồng Tháp',
    'location.hours': '⏰ Giờ mở cửa: 7:00 - 22:00 hàng ngày',
    'location.phone': '📞 Hotline: 0901 234 567',
    'location.directions': '🗺️ Chỉ Đường',
    'location.call': '📞 Gọi Ngay',

    // Menu
    'menu.coffee': 'Cà Phê',
    'menu.tea': 'Trà',
    'menu.signature': 'Signature',
    'menu.snacks': 'Ăn Vặt',
    'menu.combo': 'Combo',
    'menu.view_all': 'Xem tất cả',
    'menu.popular': 'Phổ biến',
    'menu.new': 'Mới',
    'menu.price': 'Giá',
    'menu.price_range': '30.000đ - 150.000đ',

    // Notifications
    'notify.added_to_cart': 'Đã thêm vào giỏ hàng',
    'notify.removed_from_cart': 'Đã xóa khỏi giỏ hàng',
    'notify.order_success': 'Đặt hàng thành công!',
    'notify.order_failed': 'Đặt hàng thất bại',
    'notify.login_required': 'Vui lòng đăng nhập',
    'notify.payment_success': 'Thanh toán thành công!',
    'notify.payment_failed': 'Thanh toán thất bại',
    'notify.item_added': 'Đã thêm {item} vào giỏ',
    'notify.cart_updated': 'Giỏ hàng đã cập nhật',
    'notify.network_error': 'Lỗi kết nối, vui lòng thử lại'
  },

  en: {
    // Navigation
    'nav.home': 'Home',
    'nav.menu': 'Menu',
    'nav.loyalty': 'Loyalty',
    'nav.contact': 'Contact',
    'nav.order': '📞 Book Table',
    'nav.about': 'About Us',
    'nav.reservation': 'Reservation',

    // Hero Section
    'hero.title': 'F&B Container Café',
    'hero.title.line1': 'F&B',
    'hero.title.line2': 'CONTAINER',
    'hero.tagline': 'Where Flavor Meets Design',
    'hero.subtitle': 'Specialty Coffee × Rooftop Bar × Check-in Cyberpunk',
    'hero.cta.primary': '🛒 Order Now',
    'hero.cta.secondary': '📍 View Location',
    'hero.hours': 'Open 7:00 - 22:00 Daily',
    'hero.badge': 'Open Daily | 7:00 - 22:00',
    'hero.btn.order': '☕ View Menu',
    'hero.btn.location': '📍 Get Directions',

    // Menu
    'menu.coffee': 'Coffee',
    'menu.tea': 'Tea',
    'menu.signature': 'Signature',
    'menu.snacks': 'Snacks',
    'menu.combo': 'Combo',
    'menu.view_all': 'View All',
    'menu.popular': 'Popular',
    'menu.new': 'New',
    'menu.price': 'Price',
    'menu.price_range': '30,000đ - 150,000đ',

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
    'contact.success': 'Thank you for contacting us!',
    'contact.error': 'An error occurred, please try again',

    // Language Toggle
    'lang.switch': 'Switch Language',
    'lang.switch.to_en': '🌐 EN',
    'lang.switch.to_vi': '🌐 VI',

    // Features
    'feature.specialty': 'Specialty Coffee',
    'feature.specialty.desc': 'Premium coffee from the finest coffee regions',
    'feature.rooftop': 'Rooftop Bar',
    'feature.rooftop.desc': '360° rice field panorama view in Sa Đéc',
    'feature.cyberpunk': 'Cyberpunk Space',
    'feature.cyberpunk.desc': 'Unique 3-floor container space, perfect for check-in',
    'feature.container': 'Container Design',
    'feature.container.desc': 'Unique industrial container architecture',

    // About Section
    'about.label': 'Our Story',
    'about.title': 'From Sa Đéc With Love',
    'about.desc': 'F&B Container Café was born from love for our homeland Sa Đéc. We bring a unique space with industrial container architecture combined with rooftop nature, creating an ideal destination for young people.',
    'about.highlight.1': '100% pure coffee from Buon Ma Thuot',
    'about.highlight.2': 'Rooftop bar with rice field sunset view',
    'about.highlight.3': 'Unique cyberpunk check-in space',
    'about.btn.learn': 'Learn More',

    // Menu Categories
    'menu.category.all': 'All',
    'menu.category.coffee': 'Coffee',
    'menu.category.tea': 'Tea',
    'menu.category.specialty': 'Signature Drinks',
    'menu.category.snacks': 'Snacks',
    'menu.category.combo': 'Combo',

    // Product
    'product.view_details': 'View Details',
    'product.add_to_cart': 'Add to Cart',

    // Order Modal
    'order.title': 'Order Online',
    'order.subtitle': 'Receive your order in 15-20 minutes',
    'order.tab.menu': 'Menu',
    'order.tab.cart': 'Cart',
    'order.cart.empty': 'Your cart is empty',
    'order.cart.subtotal': 'Subtotal',
    'order.cart.delivery': 'Delivery Fee',
    'order.cart.total': 'Total',
    'order.cart.checkout': '📦 Send Order via Zalo',
    'order.cart.items': 'items',
    'order.cart.remove': 'Remove',
    'order.cart.quantity': 'Quantity',
    'order.cart.note': 'Note (optional)',
    'order.cart.note.placeholder': 'e.g., Less sugar, no ice...',

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
    'loyalty.welcome': 'Welcome to F&B Loyalty Club',
    'loyalty.earned': 'Earned',
    'loyalty.next_tier': 'Points to next tier',
    'loyalty.perks': 'Perks',
    'loyalty.join': 'Join Now',

    // Checkout
    'checkout.title': 'Checkout',
    'checkout.cart': 'Shopping Cart',
    'checkout.total': 'Total',
    'checkout.payment': 'Payment Method',
    'checkout.confirm': 'Confirm Order',
    'checkout.customer_info': 'Customer Information',
    'checkout.delivery_address': 'Delivery Address',
    'checkout.delivery_method': 'Delivery Method',
    'checkout.delivery_method.pickup': 'Pickup',
    'checkout.delivery_method.delivery': 'Delivery',
    'checkout.order_summary': 'Order Summary',
    'checkout.place_order': 'Place Order',

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
    'footer.privacy': 'Privacy Policy',
    'footer.terms': 'Terms of Service',

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
    'common.yes': 'Yes',
    'common.no': 'No',
    'common.ok': 'OK',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.required': 'Required',
    'common.optional': 'Optional',

    // Accessibility
    'a11y.menu': 'Navigation menu',
    'a11y.skip': 'Skip to main content',
    'a11y.toggle_theme': 'Toggle light/dark mode',
    'a11y.open_menu': 'Open menu',
    'a11y.close_menu': 'Close menu',
    'a11y.cart': 'Shopping cart',
    'a11y.search': 'Search',
    'a11y.language': 'Switch language',

    // Order Status
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
    'order.track': 'Track Order',
    'order.history': 'Order History',
    'order.empty': 'No orders yet',
    'order.view_details': 'View Details',

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
    'notify.payment_failed': 'Payment failed',
    'notify.item_added': 'Added {item} to cart',
    'notify.cart_updated': 'Cart updated',
    'notify.network_error': 'Connection error, please try again',

    // Rooftop Section
    'rooftop.label': 'Sunset Sessions',
    'rooftop.title': 'Chill Trên Mây',
    'rooftop.desc': 'Rooftop deck with panoramic rice field views and Sa Đéc skyline. String lights, sofa seats, and specialty drinks — the ideal destination for sunset and after-work hangs.',
    'rooftop.highlight.view': 'Rice field view',
    'rooftop.highlight.lights': 'String lights',
    'rooftop.highlight.bar': 'Rooftop bar',
    'rooftop.highlight.wifi': 'WiFi全覆盖',

    // Location Section
    'location.label': 'Find Us',
    'location.title': 'In The Heart of Flower City',
    'location.address': '📍 Address: 91 Hùng Vương, Tân Phú Đông Ward, Sa Đéc, Đồng Tháp',
    'location.hours': '⏰ Opening Hours: 7:00 - 22:00 Daily',
    'location.phone': '📞 Hotline: 0901 234 567',
    'location.directions': '🗺️ Get Directions',
    'location.call': '📞 Call Now'
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
  // Use existing language-switcher button if it exists
  const existingToggle = document.getElementById('language-switcher');
  if (existingToggle) {
    // Update existing button
    updateLanguageToggle(existingToggle);
    existingToggle.addEventListener('click', () => {
      toggleLanguage();
    });
    return;
  }

  // Fallback: create new button if no existing toggle found
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
function updateLanguageToggle(customToggle) {
  // Try custom toggle first (for existing language-switcher button)
  let toggle = customToggle;

  // If no custom toggle, try existing language-switcher
  if (!toggle) {
    toggle = document.getElementById('language-switcher');
  }

  // Fallback to langToggle
  if (!toggle) {
    toggle = document.getElementById('langToggle');
  }

  if (!toggle) {
    return;
  }

  const lang = (window.I18N && window.I18N.currentLang) || _currentLang;

  // Update text content based on button type
  const langText = toggle.querySelector('.lang-text');
  if (langText) {
    langText.textContent = lang === 'vi' ? 'EN' : 'VI';
  } else {
    // For m3-chip style button, update full text
    const currentText = toggle.textContent;
    if (lang === 'vi') {
      toggle.textContent = '🌐 EN';
    } else {
      toggle.textContent = '🌐 VI';
    }
  }

  // Update data-i18n attribute
  toggle.setAttribute('data-i18n', lang === 'vi' ? 'lang.switch.to_en' : 'lang.switch.to_vi');
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
