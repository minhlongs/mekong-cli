/**
 * ═══════════════════════════════════════════════
 *  F&B CAFFE CONTAINER — Reviews Module
 *  Customer reviews with star ratings
 * ═══════════════════════════════════════════════
 *
 * SECURITY: All user inputs are sanitized using escapeHtml()
 * which uses the DOMPurify pattern (DOM-based escaping via createElement.textContent)
 *
 * Usage:
 *   import { reviews } from '/js/reviews.js';
 *
 *   // Submit review
 *   const result = await reviews.submitReview({
 *     item_id: 'coffee-001',
 *     rating: 5,
 *     comment: 'Ngon tuyệt!',
 *     customer_name: 'Nguyen Van A'
 *   });
 *
 *   // Load reviews
 *   const data = await reviews.loadReviews({ item_id: 'coffee-001' });
 *
 *   // Get stats
 *   const stats = await reviews.getStats('coffee-001');
 */

import { API_CONFIG } from './config.js';

// Debug logging configuration
const DEBUG = typeof FNB_DEBUG !== 'undefined' && FNB_DEBUG;

/**
 * Reviews API Client
 */
export const reviews = {
  /**
   * Submit a new review
   * @param {object} reviewData - Review information
   * @param {string} reviewData.item_id - Menu item ID
   * @param {number} reviewData.rating - Rating 1-5
   * @param {string} reviewData.comment - Review comment
   * @param {string} reviewData.customer_name - Customer name
   * @param {string} [reviewData.customer_email] - Customer email
   * @returns {Promise<{success: boolean, message?: string, review?: object, error?: string}>}
   */
  async submitReview(reviewData) {
    try {
      const response = await fetch(`${API_CONFIG.BASE}/api/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reviewData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to submit review');
      }

      return data;
    } catch (_error) {
      if (DEBUG) {console.error('SubmitReview error:', _error);}
      return {
        success: false,
        error: 'Lỗi kết nối: ' + _error.message,
      };
    }
  },

  /**
   * Load reviews
   * @param {object} params - Query parameters
   * @param {string} [params.item_id] - Filter by menu item
   * @param {number} [params.limit] - Max results
   * @param {number} [params.offset] - Offset
   * @returns {Promise<{success: boolean, reviews?: array, averageRating?: string, error?: string}>}
   */
  async loadReviews(params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString();
      const endpoint = queryString
        ? `/api/reviews?${queryString}`
        : '/api/reviews';

      const response = await fetch(`${API_CONFIG.BASE}${endpoint}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to load reviews');
      }

      return data;
    } catch (_error) {
      if (DEBUG) {console.error('LoadReviews error:', _error);}
      return {
        success: false,
        error: 'Lỗi kết nối: ' + _error.message,
      };
    }
  },

  /**
   * Get review statistics for a menu item
   * @param {string} itemId - Menu item ID
   * @returns {Promise<{success: boolean, stats?: object, error?: string}>}
   */
  async getStats(itemId) {
    try {
      const response = await fetch(`${API_CONFIG.BASE}/api/reviews/stats/${itemId}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to load stats');
      }

      return data;
    } catch (_error) {
      if (DEBUG) {console.error('GetStats error:', _error);}
      return {
        success: false,
        error: 'Lỗi kết nối: ' + _error.message,
      };
    }
  },
};

/**
 * Initialize reviews page
 */
export function initReviewsPage() {
  const form = document.getElementById('reviewForm');
  const reviewList = document.getElementById('reviewList');
  const menuItemSelect = document.getElementById('menuItem');
  const ratingSummary = document.getElementById('ratingSummary');

  if (!form || !reviewList) {
    if (DEBUG) {console.warn('[Reviews] Review elements not found');}
    return;
  }

  // Load menu items for selector
  loadMenuItems();

  // Load reviews
  loadAllReviews();

  // Form submission
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = form.querySelector('.btn-submit');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang gửi...';

    const formData = new FormData(form);
    const reviewData = {
      item_id: formData.get('item_id'),
      rating: parseInt(formData.get('rating')),
      comment: formData.get('comment'),
      customer_name: formData.get('customer_name'),
      customer_email: formData.get('customer_email'),
    };

    // Validation
    if (!reviewData.item_id || !reviewData.rating || !reviewData.customer_name) {
      alert('Vui lòng điền đầy đủ thông tin bắt buộc');
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
      return;
    }

    try {
      const result = await reviews.submitReview(reviewData);

      if (result.success) {
        alert('Cảm ơn bạn đã đánh giá!');
        form.reset();
        loadAllReviews(); // Reload reviews
      } else {
        alert('Có lỗi xảy ra: ' + (result.error || 'Không thể gửi đánh giá'));
      }
    } catch (_error) {
      alert('Lỗi kết nối: ' + _error.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });

  /**
   * Load menu items for selector
   */
  async function loadMenuItems() {
    try {
      const response = await fetch(`${API_CONFIG.BASE}/api/menu?available=true`);
      const data = await response.json();

      if (data.success && data.items) {
        const items = data.items;
        const grouped = {};

        items.forEach(item => {
          if (!grouped[item.category]) {
            grouped[item.category] = [];
          }
          grouped[item.category].push(item);
        });

        menuItemSelect.innerHTML = '<option value="">-- Chọn món --</option>';

        Object.keys(grouped).forEach(category => {
          const optgroup = document.createElement('optgroup');
          optgroup.label = category;

          grouped[category].forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = `${item.name} - ${formatPrice(item.price)}`;
            optgroup.appendChild(option);
          });

          menuItemSelect.appendChild(optgroup);
        });
      }
    } catch (_error) {
      if (DEBUG) {console.error('LoadMenuItems error:', _error);}
    }
  }

  /**
   * Load all reviews with stats
   */
  async function loadAllReviews() {
    reviewList.innerHTML = `
      <div class="loading">
        <div class="spinner"></div>
        <p>Đang tải đánh giá...</p>
      </div>
    `;

    try {
      const result = await reviews.loadReviews({ limit: 50 });

      if (result.success) {
        // Update rating summary
        if (result.averageRating) {
          updateRatingSummary(result);
        }

        // Render reviews
        renderReviews(result.reviews);
      } else {
        reviewList.innerHTML = '<p class="no-reviews">Không thể tải đánh giá</p>';
      }
    } catch (_error) {
      if (DEBUG) {console.error('LoadAllReviews error:', _error);}
      reviewList.innerHTML = '<p class="no-reviews">Có lỗi xảy ra khi tải đánh giá</p>';
    }
  }

  /**
   * Update rating summary UI
   */
  function updateRatingSummary(data) {
    const avg = parseFloat(data.averageRating) || 0;
    const total = data.reviews?.length || 0;

    document.getElementById('avgRating').textContent = avg.toFixed(1);
    document.getElementById('totalReviews').textContent = total;
    document.getElementById('avgStars').textContent = getStarString(avg);

    // Count by rating
    const counts = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    data.reviews?.forEach(r => {
      counts[r.rating] = (counts[r.rating] || 0) + 1;
    });

    const maxCount = Math.max(...Object.values(counts), 1);

    for (let i = 5; i >= 1; i--) {
      const count = counts[i] || 0;
      const percentage = (count / maxCount) * 100;
      document.getElementById(`count${i}`).textContent = count;
      document.getElementById(`bar${i}`).style.width = `${percentage}%`;
    }

    ratingSummary.style.display = 'flex';
  }

  /**
   * Render reviews list
   */
  function renderReviews(reviewsList) {
    if (!reviewsList || reviewsList.length === 0) {
      reviewList.innerHTML = `
        <div class="no-reviews">
          <p>Chưa có đánh giá nào</p>
          <p>Hãy là người đầu tiên chia sẻ trải nghiệm!</p>
        </div>
      `;
      return;
    }

    reviewList.innerHTML = reviewsList.map(review => `
      <div class="review-card">
        <div class="review-card-header">
          <div>
            <div class="customer-name">${escapeHtml(review.customer_name)}</div>
            <div class="rating">${getStarString(review.rating)}</div>
          </div>
          <div class="date">${formatDate(review.created_at)}</div>
        </div>
        ${review.item_id ? `<div class="review-card-item">${escapeHtml(review.item_id)}</div>` : ''}
        <div class="review-card-comment">${escapeHtml(review.comment)}</div>
      </div>
    `).join('');
  }

  /**
   * Helper: Get star string
   */
  function getStarString(rating) {
    const r = Math.round(rating);
    return '★'.repeat(r) + '☆'.repeat(5 - r);
  }

  /**
   * Helper: Format price
   */
  function formatPrice(price) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price);
  }

  /**
   * Helper: Format date
   */
  function formatDate(dateStr) {
    if (!dateStr) {return '';}
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  /**
   * Helper: Escape HTML - DOMPurify Pattern
   * Uses DOM textContent to escape special characters, preventing XSS
   */
  function escapeHtml(text) {
    if (!text) {return '';}
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Auto-init on DOMContentLoaded
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    initReviewsPage();
  });
}

// Default export
export default reviews;
