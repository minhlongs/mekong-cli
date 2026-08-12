// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/raas/sdk-preview.tsx
// Bundled in _ds_bundle.js as window.SdkPreview

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface SdkPreviewProps extends React.HTMLAttributes<HTMLDivElement> { language: string; code: string; endpoint: string; }
const SdkPreview = React.forwardRef<HTMLDivElement, SdkPreviewProps>(({ className, language, code, endpoint, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className)} {...props}>
    <div className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]">
      <span className="text-[var(-FontXs)] fontSemibold text-[var(-TextPrimary)] uppercase">{language}</span>
      <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">{endpoint}</span>
    </div>
    <pre className="p-[var(-SpacingLg)] fontMono text-[var(-FontXs)] text-[var(-AccentTeal400)] overflowXAuto">{code}</pre>
  </div>
));
SdkPreview.displayName = "SdkPreview";
export { SdkPreview };
