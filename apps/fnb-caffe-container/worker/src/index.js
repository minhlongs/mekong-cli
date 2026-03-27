/**
 * F&B Caffe Container - Cloudflare Worker
 * Main entry point - Routes dispatcher
 *
 * Enhanced with:
 * - CORS headers với whitelist support
 * - Rate limiting (100 req/min per IP cho GET, 10 req/min cho write ops)
 * - Error handling với proper HTTP status codes
 * - Health check endpoint GET /api/health
 *
 * Rate Limiting:
 * - General endpoints: 100 requests/phút
 * - Write operations (POST/PUT/PATCH/DELETE): 10 requests/phút
 * - Exempt paths: /api/health
 */

import { corsHeaders } from './middleware/cors.js';
import { rateLimiter, getRateLimitHeaders } from './middleware/rate-limiter.js';
import {
  errorResponse,
  successResponse,
  badRequest,
  notFound,
  internalError,
} from './middleware/error-handler.js';
import { getMenu, getMenuItem } from './routes/menu.js';
import {
  createOrder,
  getOrder,
  updateOrder,
  getAdminOrders,
  getStats,
} from './routes/orders.js';
import {
  registerUser,
  loginUser,
  logoutUser,
  getCurrentUser,
} from './routes/auth.js';
import {
  getReviews,
  createReview,
  getReviewStats,
} from './routes/reviews.js';
import {
  getLoyaltyTiers,
  getLoyaltyTier,
  getLoyaltyRewards,
  getLoyaltyReward,
  getLoyaltyEarningRules,
  getLoyaltyConfig,
  getLoyaltyFull,
} from './routes/loyalty.js';
import {
  createReservation,
  getReservations,
  getReservationById,
  updateReservation,
  deleteReservation,
} from './routes/reservations.js';
import {
  sendOrderConfirmation,
  sendReservationConfirmation,
} from './routes/notifications.js';
import { getHealthStatus } from './routes/health.js';
import {
  getStaff,
  getStaffById,
  createStaff,
  updateStaff,
  patchStaff,
  deleteStaff,
} from './routes/staff.js';
import {
  getInventory,
  getInventoryItem,
  getInventoryAlerts,
  getInventorySummary,
  createInventoryItem,
  updateInventory,
  resolveAlert,
} from './routes/inventory.js';
import {
  createPaymentIntent,
  handleWebhook,
  getPaymentStatus,
  getPaymentIntent,
} from './routes/payments.js';

// Debug logging configuration
const DEBUG = typeof FNB_DEBUG !== 'undefined' && FNB_DEBUG;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    const origin = request.headers.get('Origin') || '*';

    // Handle CORS preflight
    if (method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(origin, true), // Use whitelist mode
      });
    }

    try {
      // Health Check Endpoint (exempt from rate limiting)
      if (path === '/api/health' && method === 'GET') {
        return getHealthStatus(request, env);
      }

      // Rate Limiting Middleware
      const rateLimitResult = await rateLimiter(request, env);
      if (!rateLimitResult.allowed) {
        return rateLimitResult.response;
      }

      // Store rate limit info for response headers
      const rateLimitHeaders = rateLimitResult.limitInfo
        ? getRateLimitHeaders(rateLimitResult.limitInfo)
        : {};

      // Route matching
      // GET /api/menu
      if (path === '/api/menu' && method === 'GET') {
        return getMenu(request, env);
      }

      // GET /api/menu/:id
      if (path.match(/^\/api\/menu\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[3];
        return getMenuItem(request, env, id);
      }

      // POST /api/orders
      if (path === '/api/orders' && method === 'POST') {
        return createOrder(request, env);
      }

      // GET /api/orders/:id
      if (path.match(/^\/api\/orders\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[3];
        return getOrder(request, env, id);
      }

      // PATCH /api/orders/:id
      if (path.match(/^\/api\/orders\/[^/]+$/) && method === 'PATCH') {
        const id = path.split('/')[3];
        return updateOrder(request, env, id);
      }

      // GET /api/admin/orders
      if (path === '/api/admin/orders' && method === 'GET') {
        return getAdminOrders(request, env);
      }

      // GET /api/stats
      if (path === '/api/stats' && method === 'GET') {
        return getStats(request, env);
      }

      // Auth Routes
      // POST /api/auth/register
      if (path === '/api/auth/register' && method === 'POST') {
        return registerUser(request, env);
      }

      // POST /api/auth/login
      if (path === '/api/auth/login' && method === 'POST') {
        return loginUser(request, env);
      }

      // POST /api/auth/logout
      if (path === '/api/auth/logout' && method === 'POST') {
        return logoutUser(request, env);
      }

      // GET /api/auth/me
      if (path === '/api/auth/me' && method === 'GET') {
        return getCurrentUser(request, env);
      }

      // Reviews Routes
      // GET /api/reviews
      if (path === '/api/reviews' && method === 'GET') {
        return getReviews(request, env);
      }

      // POST /api/reviews
      if (path === '/api/reviews' && method === 'POST') {
        return createReview(request, env);
      }

      // GET /api/reviews/stats/:item_id
      if (path.match(/^\/api\/reviews\/stats\/[^/]+$/) && method === 'GET') {
        const itemId = path.split('/')[4];
        return getReviewStats(request, env, itemId);
      }

      // Loyalty Routes
      // GET /api/loyalty/full
      if (path === '/api/loyalty/full' && method === 'GET') {
        return getLoyaltyFull(request, env);
      }

      // GET /api/loyalty/tiers
      if (path === '/api/loyalty/tiers' && method === 'GET') {
        return getLoyaltyTiers(request, env);
      }

      // GET /api/loyalty/tiers/:id
      if (path.match(/^\/api\/loyalty\/tiers\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[4];
        return getLoyaltyTier(request, env, id);
      }

      // GET /api/loyalty/rewards
      if (path === '/api/loyalty/rewards' && method === 'GET') {
        return getLoyaltyRewards(request, env);
      }

      // GET /api/loyalty/rewards/:id
      if (path.match(/^\/api\/loyalty\/rewards\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[4];
        return getLoyaltyReward(request, env, id);
      }

      // GET /api/loyalty/earning-rules
      if (path === '/api/loyalty/earning-rules' && method === 'GET') {
        return getLoyaltyEarningRules(request, env);
      }

      // GET /api/loyalty/config
      if (path === '/api/loyalty/config' && method === 'GET') {
        return getLoyaltyConfig(request, env);
      }

      // Reservation Routes
      // POST /api/reservations
      if (path === '/api/reservations' && method === 'POST') {
        return createReservation(request, env);
      }

      // GET /api/reservations
      if (path === '/api/reservations' && method === 'GET') {
        return getReservations(request, env);
      }

      // GET /api/reservations/:id
      if (path.match(/^\/api\/reservations\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[3];
        return getReservationById(request, env, id);
      }

      // PATCH /api/reservations/:id
      if (path.match(/^\/api\/reservations\/[^/]+$/) && method === 'PATCH') {
        const id = path.split('/')[3];
        return updateReservation(request, env, id);
      }

      // DELETE /api/reservations/:id
      if (path.match(/^\/api\/reservations\/[^/]+$/) && method === 'DELETE') {
        const id = path.split('/')[3];
        return deleteReservation(request, env, id);
      }

      // Notification Routes
      // POST /api/notify/order-confirmation
      if (path === '/api/notify/order-confirmation' && method === 'POST') {
        return sendOrderConfirmation(request, env);
      }

      // POST /api/notify/reservation-confirmation
      if (path === '/api/notify/reservation-confirmation' && method === 'POST') {
        return sendReservationConfirmation(request, env);
      }

      // Staff Routes
      // GET /api/staff
      if (path === '/api/staff' && method === 'GET') {
        return getStaff(request, env);
      }

      // POST /api/staff
      if (path === '/api/staff' && method === 'POST') {
        return createStaff(request, env);
      }

      // GET /api/staff/:id
      if (path.match(/^\/api\/staff\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[3];
        return getStaffById(request, env, id);
      }

      // PUT /api/staff/:id
      if (path.match(/^\/api\/staff\/[^/]+$/) && method === 'PUT') {
        const id = path.split('/')[3];
        return updateStaff(request, env, id);
      }

      // PATCH /api/staff/:id
      if (path.match(/^\/api\/staff\/[^/]+$/) && method === 'PATCH') {
        const id = path.split('/')[3];
        return patchStaff(request, env, id);
      }

      // DELETE /api/staff/:id
      if (path.match(/^\/api\/staff\/[^/]+$/) && method === 'DELETE') {
        const id = path.split('/')[3];
        return deleteStaff(request, env, id);
      }

      // Inventory Routes
      // GET /api/inventory
      if (path === '/api/inventory' && method === 'GET') {
        return getInventory(request, env);
      }

      // GET /api/inventory/alerts
      if (path === '/api/inventory/alerts' && method === 'GET') {
        return getInventoryAlerts(request, env);
      }

      // GET /api/inventory/summary
      if (path === '/api/inventory/summary' && method === 'GET') {
        return getInventorySummary(request, env);
      }

      // POST /api/inventory
      if (path === '/api/inventory' && method === 'POST') {
        return createInventoryItem(request, env);
      }

      // GET /api/inventory/:id
      if (path.match(/^\/api\/inventory\/[^/]+$/) && method === 'GET') {
        const id = path.split('/')[3];
        // Check for alert resolve subpath
        if (path.includes('/resolve')) {
          return resolveAlert(request, env, id);
        }
        return getInventoryItem(request, env, id);
      }

      // PUT /api/inventory/:id
      if (path.match(/^\/api\/inventory\/[^/]+$/) && method === 'PUT') {
        const id = path.split('/')[3];
        return updateInventory(request, env, id);
      }

      // Payment Routes
      // POST /api/payment/create-url
      if (path === '/api/payment/create-url' && method === 'POST') {
        return createPaymentIntent(request, env);
      }

      // POST /api/payment/webhook
      if (path === '/api/payment/webhook' && method === 'POST') {
        return handleWebhook(request, env);
      }

      // GET /api/payment/status/:orderId
      if (path.match(/^\/api\/payment\/status\/[^/]+$/) && method === 'GET') {
        const orderId = path.split('/')[4];
        return getPaymentStatus(request, env, orderId);
      }

      // GET /api/payment/intent/:paymentIntentId
      if (path.match(/^\/api\/payment\/intent\/[^/]+$/) && method === 'GET') {
        const paymentIntentId = path.split('/')[4];
        return getPaymentIntent(request, env, paymentIntentId);
      }

      // 404 for unmatched routes
      return notFound('Endpoint not found');

    } catch (error) {
      if (DEBUG) {console.error('Worker error:', error);}
      return internalError(error.message, DEBUG);
    }
  },
};
