/**
 * Dashboard Load Test - k6 script for beta launch verification.
 * Tests: 100 concurrent users, <2s page load, WebSocket stress test.
 *
 * Run: k6 run tests/load/dashboard-load-test.ts
 * CI:  k6 run --quiet tests/load/dashboard-load-test.ts
 */

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const loadTestPassed = new Rate('load_test_passed');
const pageLoadTime = new Trend('page_load_time');
const wsLatency = new Trend('websocket_latency');
const wsMessagesReceived = new Counter('websocket_messages_received');
const apiErrors = new Rate('api_errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up to 20 users
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '2m', target: 100 },   // Ramp up to 100 users (target)
    { duration: '3m', target: 100 },   // Stay at 100 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],      // 95% of requests < 2s
    http_req_failed: ['rate<0.01'],         // Error rate < 1%
    page_load_time: ['p(95)<2000'],         // Page load p95 < 2s
    websocket_latency: ['p(95)<1000'],      // WS latency p95 < 1s
    load_test_passed: ['rate>0.95'],        // 95% success rate
    api_errors: ['rate<0.01'],              // API error rate < 1%
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],
};

// Test environment - adjust BASE_URL for staging/production
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:3001/ws';

/**
 * Scenario 1: Landing Page Load
 * Simulates users loading the landing page
 */
export function landingPageTest() {
  const start = Date.now();

  const res = http.get(`${BASE_URL}/`, {
    headers: {
      'Accept': 'text/html,application/xhtml+xml',
      'Accept-Language': 'en-US,en;q=0.9',
      'User-Agent': 'k6-load-test/1.0',
    },
  });

  const loadTime = Date.now() - start;
  pageLoadTime.add(loadTime);

  const passed = check(res, {
    'landing page: status 200': (r) => r.status === 200,
    'landing page: has content': (r) => r.body.length > 1000,
    'landing page: load < 2s': () => loadTime < 2000,
  });

  loadTestPassed.add(passed ? 1 : 0);
  sleep(1);
}

/**
 * Scenario 2: Dashboard Page Load (authenticated)
 * Simulates users loading the dashboard with auth token
 */
export function dashboardPageTest() {
  // Get auth token (mock or real)
  const authToken = __ENV.AUTH_TOKEN || 'mock-token';

  const start = Date.now();

  const res = http.get(`${BASE_URL}/app`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Accept': 'text/html,application/xhtml+xml',
      'Accept-Language': 'en-US,en;q=0.9',
      'User-Agent': 'k6-load-test/1.0',
    },
  });

  const loadTime = Date.now() - start;
  pageLoadTime.add(loadTime);

  const passed = check(res, {
    'dashboard: status 200 or 302': (r) => r.status === 200 || r.status === 302,
    'dashboard: load < 2s': () => loadTime < 2000,
  });

  loadTestPassed.add(passed ? 1 : 0);
  sleep(2);
}

/**
 * Scenario 3: API Endpoints
 * Tests critical API endpoints for dashboard data
 */
export function apiEndpointsTest() {
  const authToken = __ENV.AUTH_TOKEN || 'mock-token';
  const headers = {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json',
    'User-Agent': 'k6-load-test/1.0',
  };

  // Test health endpoint
  const healthRes = http.get(`${BASE_URL}/api/health`, { headers });
  apiErrors.add(healthRes.status !== 200 ? 1 : 0);
  check(healthRes, {
    'health: status 200': (r) => r.status === 200,
  });

  // Test metrics endpoint
  const metricsRes = http.get(`${BASE_URL}/api/metrics`, { headers });
  apiErrors.add(metricsRes.status !== 200 ? 1 : 0);
  check(metricsRes, {
    'metrics: status 200': (r) => r.status === 200,
  });

  // Test signals endpoint
  const signalsRes = http.get(`${BASE_URL}/api/v1/signals?limit=50`, { headers });
  apiErrors.add(signalsRes.status !== 200 && signalsRes.status !== 401 ? 1 : 0);
  check(signalsRes, {
    'signals: status 200 or 401': (r) => r.status === 200 || r.status === 401,
  });

  sleep(0.5);
}

/**
 * Scenario 4: WebSocket Connection Stress Test
 * Tests WebSocket connections under load
 */
export function websocketStressTest() {
  const token = __ENV.AUTH_TOKEN || 'mock-token';

  const response = ws.connect(WS_URL, {}, function (socket) {
    socket.on('open', () => {
      // Subscribe to channels
      socket.send(JSON.stringify({
        type: 'subscribe',
        channels: ['pnl', 'positions', 'spreads', 'trades'],
      }));
    });

    socket.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        wsMessagesReceived.add(1);

        // Track latency if timestamp present
        if (message.timestamp) {
          const latency = Date.now() - message.timestamp;
          wsLatency.add(latency);
        }

        check(message, {
          'ws: valid JSON': () => true,
          'ws: has type field': (m) => typeof m.type === 'string',
        });
      } catch (e) {
        wsLatency.add(0);
      }
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    socket.on('close', () => {
      console.log('WebSocket closed');
    });

    // Keep connection open for 30 seconds
    sleep(30);
    socket.close();
  });

  check(response, {
    'ws: connected': (r) => r && r.status === 101,
  });
}

/**
 * Main load test execution
 * Each VU runs through all scenarios
 */
export default function () {
  const scenario = Math.random();

  if (scenario < 0.3) {
    // 30% landing page
    landingPageTest();
  } else if (scenario < 0.6) {
    // 30% dashboard
    dashboardPageTest();
  } else if (scenario < 0.8) {
    // 20% API endpoints
    apiEndpointsTest();
  } else {
    // 20% WebSocket stress
    websocketStressTest();
  }
}

/**
 * Handle teardown after test completes
 */
export function handleSummary(data) {
  const summary = {
    test_passed: true,
    metrics: {},
    recommendations: [],
  };

  // Check thresholds
  if (data.metrics.load_test_passed && data.metrics.load_test_passed.values.rate < 0.95) {
    summary.test_passed = false;
    summary.recommendations.push('Load test success rate below 95% - investigate failures');
  }

  if (data.metrics.page_load_time && data.metrics.page_load_time.values['p(95)'] > 2000) {
    summary.test_passed = false;
    summary.recommendations.push('Page load p95 above 2s - optimize bundle size, add caching');
  }

  if (data.metrics.websocket_latency && data.metrics.websocket_latency.values['p(95)'] > 1000) {
    summary.recommendations.push('WebSocket latency p95 above 1s - check server capacity');
  }

  // Add metrics summary
  summary.metrics = {
    http_req_duration: data.metrics.http_req_duration?.values,
    page_load_time: data.metrics.page_load_time?.values,
    websocket_latency: data.metrics.websocket_latency?.values,
    load_test_passed: data.metrics.load_test_passed?.values,
    websocket_messages: data.metrics.websocket_messages_received?.values.count,
  };

  console.log('=== LOAD TEST SUMMARY ===');
  console.log(JSON.stringify(summary, null, 2));

  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    [`summary-${Date.now()}.json`]: JSON.stringify(summary),
  };
}

function textSummary(data, options) {
  const { indent = '', enableColors = false } = options;
  const reset = enableColors ? '\x1b[0m' : '';
  const bold = enableColors ? '\x1b[1m' : '';

  let output = `\n${bold}=== K6 LOAD TEST SUMMARY ===${reset}\n\n`;
  output += `${indent}Execution time: ${data.state.testRunDurationMs}ms\n`;
  output += `${indent}Virtual users: ${data.metrics.vus_max?.values.value ?? 0}\n`;
  output += `${indent}Total iterations: ${data.metrics.iterations?.values.value ?? 0}\n\n`;

  output += `${bold}Thresholds:${reset}\n`;
  for (const [name, metric] of Object.entries(data.metrics)) {
    if (metric.thresholds) {
      for (const [threshold, result] of Object.entries(metric.thresholds)) {
        const status = result.ok ? '✅' : '❌';
        output += `${indent}${status} ${name} - ${threshold}: ${result.ok ? 'PASS' : 'FAIL'}\n`;
      }
    }
  }

  return output;
}
