// Mock Analytics client until @agencyos/vibe-analytics is available
// This will be replaced with actual SDK implementation

export const analytics = {
  track: (event: { event: string; properties?: Record<string, any> }) => {
    if (typeof window === 'undefined') return;
    console.log('Track event:', event);
  },
  page: (data: { path?: string; url?: string; referrer?: string }) => {
    if (typeof window === 'undefined') return;
    console.log('Track page:', data);
  },
  identify: (data: { userId: string; traits?: Record<string, any> }) => {
    console.log('Identify user:', data);
  },
};

export const trackEvent = (event: string, properties?: Record<string, any>) => {
  if (typeof window === 'undefined') return;

  analytics.track({
    event,
    properties: {
      ...properties,
      url: window.location.href,
      path: window.location.pathname,
      referrer: document.referrer,
      timestamp: new Date().toISOString(),
    },
  });
};

export const trackPageView = (path?: string) => {
  if (typeof window === 'undefined') return;

  analytics.page({
    path: path || window.location.pathname,
    url: window.location.href,
    referrer: document.referrer,
  });
};

export const identifyUser = (userId: string, traits?: Record<string, any>) => {
  analytics.identify({
    userId,
    traits,
  });
};
