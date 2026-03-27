/**
 * CORS Middleware
 * Cross-Origin Resource Sharing headers cho F&B Caffe Container API
 */

// Allowed origins (có thể override qua env vars)
const ALLOWED_ORIGINS = [
  'https://fnbcontainer.vn',
  'https://www.fnbcontainer.vn',
  'https://fnb-caffe-container.pages.dev',
  'http://localhost:8000',
  'http://127.0.0.1:8000',
];

/**
 * Kiểm tra origin có được allow không
 * @param {string} origin - Origin từ request
 * @returns {boolean} true nếu được allow
 */
export function isAllowedOrigin(origin) {
  if (!origin) return false;
  return ALLOWED_ORIGINS.includes(origin);
}

/**
 * Tạo CORS headers
 * @param {string} origin - Origin domain từ request
 * @param {boolean} useWhitelist - Có dùng whitelist không (default: false)
 * @returns {Record<string, string>} CORS headers object
 */
export function corsHeaders(origin = '*', useWhitelist = false) {
  // Nếu dùng whitelist và origin hợp lệ
  let allowedOrigin = origin;
  if (useWhitelist) {
    allowedOrigin = isAllowedOrigin(origin) ? origin : 'null';
  } else if (origin === '*' || !origin) {
    allowedOrigin = '*';
  }

  return {
    'Access-Control-Allow-Origin': allowedOrigin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Session-ID, X-RateLimit-IP',
    'Access-Control-Allow-Credentials': useWhitelist ? 'true' : 'false',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Expose-Headers': 'X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset',
  };
}

/**
 * Tạo JSON response với CORS headers
 * @param {any} data - Response data
 * @param {number} status - HTTP status code
 * @param {Record<string, string>} headers - Custom headers
 * @returns {Response} Response object
 */
export function jsonResponse(data, status = 200, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders(),
      ...headers,
    },
  });
}

/**
 * Tạo error response
 * @param {string} message - Error message
 * @param {number} status - HTTP status code
 * @param {Record<string, string>} headers - Custom headers
 * @returns {Response} Error response
 */
export function errorResponse(message, status = 400, headers = {}) {
  return jsonResponse({ success: false, error: message }, status, headers);
}
