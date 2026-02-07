"use client";

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { trackPageView } from '@/lib/vibe-analytics-client';

export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Track initial page view
    trackPageView(pathname);
  }, [pathname, searchParams]);

  return <>{children}</>;
}
