import type { Product } from "./catalog.js";
import type { ProductCatalog } from "./catalog.js";

export interface StorefrontResponse {
  status: number;
  contentType: string;
  body: string;
}

export function generateStorefrontHTML(products: Product[]): string {
  const cards = products
    .filter((p) => p.active)
    .map(
      (p) => `
  <div class="product-card" data-id="${p.id}" data-tier="${p.tier}">
    <h2>${p.name}</h2>
    <p>${p.description}</p>
    <div class="price">$${p.basePriceUsd}<span>/mo</span></div>
    <ul>${p.features.map((f) => `<li>${f}</li>`).join("")}</ul>
    <a href="/checkout?product=${p.id}" class="cta-btn">Get Started</a>
  </div>`
    )
    .join("\n");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OpenClaw Marketplace</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; background: #0a0a0a; color: #fff; }
    .products { display: flex; gap: 1.5rem; flex-wrap: wrap; justify-content: center; padding: 2rem; }
    .product-card { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 2rem; width: 280px; }
    .product-card h2 { margin: 0 0 0.5rem; }
    .price { font-size: 2rem; font-weight: bold; color: #22d3ee; margin: 1rem 0; }
    .price span { font-size: 1rem; color: #888; }
    ul { padding-left: 1.2rem; color: #aaa; }
    .cta-btn { display: block; text-align: center; background: #22d3ee; color: #000; padding: 0.75rem; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 1.5rem; }
  </style>
</head>
<body>
  <div class="products">${cards}</div>
</body>
</html>`;
}

export function generateStorefrontJSON(products: Product[]): object {
  return {
    success: true,
    data: products.filter((p) => p.active).map((p) => ({
      id: p.id,
      name: p.name,
      description: p.description,
      priceUsd: p.basePriceUsd,
      tier: p.tier,
      features: p.features,
      checkoutUrl: `/checkout?product=${p.id}`,
    })),
    count: products.filter((p) => p.active).length,
  };
}

export function generateEmbedWidget(products: Product[]): string {
  const activeProducts = products.filter((p) => p.active);
  const items = activeProducts
    .map((p) => `<div style="padding:1rem;border:1px solid #333;border-radius:8px;margin:0.5rem 0"><strong>${p.name}</strong> — $${p.basePriceUsd}/mo <a href="/checkout?product=${p.id}" style="color:#22d3ee;margin-left:1rem">Buy</a></div>`)
    .join("");

  return `<div id="openclaw-widget" style="font-family:system-ui,sans-serif;max-width:400px">${items}<script>/* OpenClaw Marketplace Widget v0.1.0 */</script></div>`;
}

export function handleStorefrontRequest(
  path: string,
  catalog: ProductCatalog
): StorefrontResponse {
  const products = catalog.listProducts({ active: true });

  if (path === "/products") {
    return {
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(generateStorefrontJSON(products)),
    };
  }

  if (path === "/widget") {
    return {
      status: 200,
      contentType: "text/html",
      body: generateEmbedWidget(products),
    };
  }

  const idMatch = path.match(/^\/products\/([^/]+)$/);
  if (idMatch) {
    const product = catalog.getProduct(idMatch[1]);
    if (!product) {
      return { status: 404, contentType: "application/json", body: JSON.stringify({ error: "Product not found" }) };
    }
    return {
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: product }),
    };
  }

  return { status: 404, contentType: "application/json", body: JSON.stringify({ error: "Not found" }) };
}
