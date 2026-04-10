import { ChevronRight } from "lucide-react";

interface BreadcrumbProps {
  /** Full path string, e.g. "~/project/src/auth.ts" */
  path: string;
  onNavigate?: (segment: string, index: number) => void;
}

/**
 * File path breadcrumb for the top bar center.
 * Each segment is clickable; last segment is styled bolder.
 */
export function Breadcrumb({ path, onNavigate }: BreadcrumbProps) {
  const segments = path.replace(/^~\//, "~/").split("/").filter(Boolean);

  // Re-prefix first segment with ~/ if path starts with ~/
  const displaySegments = path.startsWith("~/")
    ? ["~", ...segments.slice(1)]
    : segments;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.125rem",
        fontSize: "0.8rem",
        color: "var(--text-secondary)",
        overflow: "hidden",
        maxWidth: "100%",
      }}
    >
      {displaySegments.map((seg, i) => {
        const isLast = i === displaySegments.length - 1;
        return (
          <span key={i} style={{ display: "flex", alignItems: "center", gap: "0.125rem", minWidth: 0 }}>
            {i > 0 && (
              <ChevronRight
                size={12}
                style={{ color: "var(--text-muted)", flexShrink: 0 }}
              />
            )}
            <button
              onClick={() => onNavigate?.(seg, i)}
              title={seg}
              style={{
                background: "none",
                border: "none",
                cursor: onNavigate ? "pointer" : "default",
                color: isLast ? "var(--text-primary)" : "var(--text-secondary)",
                fontWeight: isLast ? 600 : 400,
                fontSize: "inherit",
                padding: "0 0.125rem",
                maxWidth: isLast ? "none" : "120px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                borderRadius: "0.2rem",
                transition: "color 0.1s",
              }}
            >
              {seg}
            </button>
          </span>
        );
      })}
    </div>
  );
}
