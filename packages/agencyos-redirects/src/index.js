/**
 * Redirect worker for old agencyos.network subdomains.
 * Routes old subdomain traffic to the unified agencyos.network site.
 */
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const host = url.hostname;
    const path = url.pathname;

    const redirectMap = {
      'sophia.agencyos.network': 'https://agencyos.network/',
      'landing.agencyos.network': 'https://agencyos.network/',
      'app.agencyos.network': `https://agencyos.network/dashboard${path}`,
      'dashboard.agencyos.network': `https://agencyos.network/dashboard${path}`,
      'docs.agencyos.network': `https://agencyos.network/docs${path}`,
    };

    const target = redirectMap[host];
    if (target) {
      return Response.redirect(target, 301);
    }

    return new Response('Not Found', { status: 404 });
  },
};
