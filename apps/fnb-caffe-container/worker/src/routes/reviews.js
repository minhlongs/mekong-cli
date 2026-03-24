/**
 * Reviews Routes
 * API endpoints cho customer reviews operations
 */

import { jsonResponse, errorResponse } from '../middleware/cors.js';

// Debug logging configuration
const DEBUG = typeof FNB_DEBUG !== 'undefined' && FNB_DEBUG;

/**
 * GET /api/reviews
 * Query params: item_id (optional), limit, offset
 * Returns all reviews or reviews for a specific menu item
 */
export async function getReviews(request, env) {
  try {
    const url = new URL(request.url);
    const itemId = url.searchParams.get('item_id');
    const limit = url.searchParams.get('limit') || '50';
    const offset = url.searchParams.get('offset') || '0';

    let query = 'SELECT * FROM reviews WHERE 1=1';
    const params = [];

    if (itemId) {
      query += ' AND item_id = ?';
      params.push(itemId);
    }

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
    params.push(parseInt(limit), parseInt(offset));

    const { results } = await env.FNB_DB.prepare(query).bind(...params).all();

    const reviews = results.map(review => ({
      ...review,
      rating: parseInt(review.rating),
    }));

    // Get total count
    const countQuery = 'SELECT COUNT(*) as total FROM reviews WHERE 1=1' +
      (itemId ? ' AND item_id = ?' : '');

    const countParams = itemId ? [itemId] : [];
    const { results: countResult } = await env.FNB_DB.prepare(countQuery).bind(...countParams).all();
    const total = countResult[0]?.total || 0;

    // Calculate average rating if item_id is provided
    let averageRating = null;
    if (itemId) {
      const { results: avgResult } = await env.FNB_DB
        .prepare('SELECT AVG(rating) as avg, COUNT(*) as count FROM reviews WHERE item_id = ?')
        .bind(itemId)
        .all();
      if (avgResult[0]?.avg) {
        averageRating = parseFloat(avgResult[0].avg).toFixed(1);
      }
    }

    return jsonResponse({
      success: true,
      reviews,
      pagination: {
        total: parseInt(total),
        limit: parseInt(limit),
        offset: parseInt(offset),
      },
      averageRating,
    });
  } catch (error) {
    if (DEBUG) {console.error('GetReviews error:', error);}
    return errorResponse('Failed to fetch reviews: ' + error.message, 500);
  }
}

/**
 * POST /api/reviews
 * Create a new review
 * Body: item_id, rating (1-5), comment, customer_name, customer_email (optional)
 */
export async function createReview(request, env) {
  try {
    const body = await request.json();
    const { item_id, rating, comment, customer_name, customer_email } = body;

    // Validation
    if (!item_id || !rating || !customer_name) {
      return errorResponse('Missing required fields: item_id, rating, customer_name', 400);
    }

    if (rating < 1 || rating > 5) {
      return errorResponse('Rating must be between 1 and 5', 400);
    }

    // Generate unique ID
    const reviewId = `rev_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Insert into database
    await env.FNB_DB.prepare(`
      INSERT INTO reviews (id, item_id, rating, comment, customer_name, customer_email, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    `).bind(reviewId, item_id, parseInt(rating), comment || null, customer_name, customer_email || null).run();

    if (DEBUG) {console.log('[Reviews] Created review:', reviewId);}

    return jsonResponse({
      success: true,
      message: 'Review created successfully',
      review: {
        id: reviewId,
        item_id,
        rating: parseInt(rating),
        comment,
        customer_name,
        customer_email,
      },
    });
  } catch (error) {
    if (DEBUG) {console.error('CreateReview error:', error);}
    return errorResponse('Failed to create review: ' + error.message, 500);
  }
}

/**
 * GET /api/reviews/stats/:item_id
 * Get review statistics for a menu item
 */
export async function getReviewStats(request, env, itemId) {
  try {
    if (!itemId) {
      return errorResponse('Item ID is required', 400);
    }

    const { results } = await env.FNB_DB.prepare(`
      SELECT
        COUNT(*) as total,
        AVG(rating) as average,
        SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as five_star,
        SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as four_star,
        SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as three_star,
        SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as two_star,
        SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as one_star
      FROM reviews
      WHERE item_id = ?
    `).bind(itemId).all();

    const stats = results[0] || {
      total: 0,
      average: 0,
      five_star: 0,
      four_star: 0,
      three_star: 0,
      two_star: 0,
      one_star: 0,
    };

    return jsonResponse({
      success: true,
      stats: {
        total: parseInt(stats.total),
        average: stats.average ? parseFloat(stats.average).toFixed(1) : '0.0',
        five_star: parseInt(stats.five_star),
        four_star: parseInt(stats.four_star),
        three_star: parseInt(stats.three_star),
        two_star: parseInt(stats.two_star),
        one_star: parseInt(stats.one_star),
      },
    });
  } catch (error) {
    if (DEBUG) {console.error('GetReviewStats error:', error);}
    return errorResponse('Failed to fetch review stats: ' + error.message, 500);
  }
}
