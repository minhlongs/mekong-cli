/**
 * Landing page route — marketing page served from the Worker
 */

import { Hono } from 'hono';
import type { Env } from '../index';

export const landing = new Hono<{ Bindings: Env }>();

const FEATURES = [
  ['AI Missions', 'Submit goals, get results. AI executes autonomously.'],
  ['Team Collaboration', 'Multi-seat workspaces with role-based access.'],
  ['Multi-Project', 'Manage unlimited projects from one dashboard.'],
  ['Referral Program', 'Earn credits for every referral that converts.'],
  ['SDK & API', 'Full REST API + TypeScript SDK for integrations.'],
  ['Enterprise Ready', 'SSO, audit logs, SLA, and dedicated support.'],
];

const PRICING = [
  ['Starter', '$49', '200 MCU/mo', '/billing/checkout?plan=starter'],
  ['Pro', '$149', '1,000 MCU/mo', '/billing/checkout?plan=pro'],
  ['Enterprise', '$499', 'Unlimited MCU', '/billing/checkout?plan=enterprise'],
];

/** GET / — Marketing landing page */
landing.get('/', (c) => {
  const featureCards = FEATURES.map(([title, desc]) =>
    `<div class="card"><h3>${title}</h3><p>${desc}</p></div>`
  ).join('');

  const pricingCards = PRICING.map(([tier, price, credits, link], i) =>
    `<div class="plan${i === 1 ? ' featured' : ''}">
      <div class="tier">${tier}</div>
      <div class="price">${price}<span>/mo</span></div>
      <div class="credits">${credits}</div>
      <a href="${link}" class="btn${i === 1 ? ' btn-primary' : ' btn-outline'}">Get Started</a>
    </div>`
  ).join('');

  return c.html(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mekong RaaS — Robot-as-a-Service</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:system-ui,sans-serif;background:#0a0a0a;color:#e5e5e5;line-height:1.6}
    a{color:#06b6d4;text-decoration:none}
    .container{max-width:1100px;margin:0 auto;padding:0 20px}
    /* Nav */
    nav{border-bottom:1px solid #1f1f1f;padding:16px 0}
    nav .inner{display:flex;justify-content:space-between;align-items:center}
    .logo{font-size:1.2rem;font-weight:700;color:#06b6d4}
    .nav-links{display:flex;gap:24px;font-size:.9rem}
    /* Hero */
    .hero{text-align:center;padding:80px 20px 60px}
    .hero h1{font-size:clamp(2rem,5vw,3.5rem);font-weight:800;line-height:1.2;margin-bottom:16px}
    .hero h1 span{color:#06b6d4}
    .hero p{font-size:1.15rem;color:#a3a3a3;max-width:560px;margin:0 auto 32px}
    .hero-btns{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
    .btn{display:inline-block;padding:12px 28px;border-radius:8px;font-weight:600;font-size:.95rem;cursor:pointer;transition:opacity .2s}
    .btn-primary{background:#06b6d4;color:#0a0a0a}
    .btn-primary:hover{opacity:.85}
    .btn-outline{border:1px solid #404040;color:#e5e5e5}
    .btn-outline:hover{border-color:#06b6d4;color:#06b6d4}
    /* Stats */
    .stats{background:#111;border-top:1px solid #1f1f1f;border-bottom:1px solid #1f1f1f;padding:24px 0}
    .stats .inner{display:flex;justify-content:space-around;flex-wrap:wrap;gap:16px;text-align:center}
    .stat-val{font-size:1.8rem;font-weight:700;color:#06b6d4}
    .stat-label{font-size:.85rem;color:#737373}
    /* Features */
    section{padding:64px 0}
    h2{font-size:1.8rem;font-weight:700;text-align:center;margin-bottom:8px}
    .subtitle{text-align:center;color:#737373;margin-bottom:40px}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px}
    .card{background:#111;border:1px solid #1f1f1f;border-radius:12px;padding:24px}
    .card h3{color:#06b6d4;margin-bottom:8px;font-size:1rem}
    .card p{color:#a3a3a3;font-size:.9rem}
    /* Pricing */
    .pricing-grid{display:flex;gap:20px;justify-content:center;flex-wrap:wrap}
    .plan{background:#111;border:1px solid #1f1f1f;border-radius:12px;padding:28px 24px;text-align:center;min-width:220px;flex:1;max-width:300px}
    .plan.featured{border-color:#06b6d4}
    .tier{font-size:.85rem;font-weight:600;color:#737373;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}
    .price{font-size:2.2rem;font-weight:800;margin-bottom:4px}
    .price span{font-size:1rem;color:#737373;font-weight:400}
    .credits{color:#a3a3a3;font-size:.9rem;margin-bottom:24px}
    .plan .btn{width:100%;text-align:center}
    /* CTA */
    .cta{background:#06b6d433;border:1px solid #06b6d455;border-radius:16px;padding:48px 24px;text-align:center;margin:0 0 64px}
    .cta h2{margin-bottom:12px}
    .cta p{color:#a3a3a3;margin-bottom:28px}
    /* Footer */
    footer{border-top:1px solid #1f1f1f;padding:32px 0;text-align:center}
    footer .links{display:flex;gap:24px;justify-content:center;margin-bottom:12px;flex-wrap:wrap;font-size:.9rem}
    footer .copy{color:#525252;font-size:.8rem}
    @media(max-width:600px){
      .hero{padding:48px 16px 40px}
      .pricing-grid{flex-direction:column;align-items:center}
    }
  </style>
</head>
<body>
<nav><div class="container inner">
  <span class="logo">Mekong RaaS</span>
  <div class="nav-links">
    <a href="/docs">Docs</a>
    <a href="/playground">Playground</a>
    <a href="/billing/checkout" class="btn btn-primary" style="padding:8px 18px">Start Free</a>
  </div>
</div></nav>

<div class="hero">
  <h1>Mekong RaaS —<br><span>Robot-as-a-Service</span></h1>
  <p>AI-Operated Business Platform. Submit a mission, get results.</p>
  <div class="hero-btns">
    <a href="/billing/checkout" class="btn btn-primary">Get Started</a>
    <a href="/docs" class="btn btn-outline">View Docs</a>
  </div>
</div>

<div class="stats"><div class="container inner">
  <div><div class="stat-val">10K+</div><div class="stat-label">Missions Completed</div></div>
  <div><div class="stat-val">99.9%</div><div class="stat-label">Uptime SLA</div></div>
  <div><div class="stat-val">&lt;2s</div><div class="stat-label">Avg Response</div></div>
  <div><div class="stat-val">500+</div><div class="stat-label">Active Teams</div></div>
</div></div>

<section><div class="container">
  <h2>Everything You Need</h2>
  <p class="subtitle">Six pillars of the AI-operated business platform</p>
  <div class="grid">${featureCards}</div>
</div></section>

<section style="background:#050505"><div class="container">
  <h2>Simple Pricing</h2>
  <p class="subtitle">Pay for what you use. No hidden fees.</p>
  <div class="pricing-grid">${pricingCards}</div>
</div></section>

<section><div class="container">
  <div class="cta">
    <h2>Ready to automate your business?</h2>
    <p>Start with 200 free MCU. No credit card required.</p>
    <a href="/billing/checkout" class="btn btn-primary">Start Free Trial</a>
  </div>
</div></section>

<footer><div class="container">
  <div class="links">
    <a href="/docs">Documentation</a>
    <a href="/playground">API Playground</a>
    <a href="/v1/billing/pricing">Pricing API</a>
    <a href="mailto:support@mekong.ai">Support</a>
  </div>
  <div class="copy">&copy; 2026 Mekong RaaS. All rights reserved.</div>
</div></footer>
</body>
</html>`);
});
