"use client";

import { useCallback, useRef } from "react";

interface PanelResizerProps {
  /** Callback with new right panel width in px */
  onResize: (newWidth: number) => void;
  /** Min width of right panel in px (default 280) */
  minWidth?: number;
  /** Max width of right panel in px (default 480) */
  maxWidth?: number;
}

/**
 * Vertical drag handle for resizing the right panel.
 * Placed between center and right panels.
 * On drag: computes new right-panel width from mouse position.
 */
export function PanelResizer({
  onResize,
  minWidth = 280,
  maxWidth = 480,
}: PanelResizerProps) {
  const isDragging = useRef(false);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isDragging.current = true;

      const startX = e.clientX;
      const containerWidth = window.innerWidth;

      function onMouseMove(ev: MouseEvent) {
        if (!isDragging.current) return;
        // Right panel width = distance from cursor to right edge
        const newWidth = containerWidth - ev.clientX;
        const clamped = Math.min(maxWidth, Math.max(minWidth, newWidth));
        onResize(clamped);
      }

      function onMouseUp() {
        isDragging.current = false;
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }

      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    },
    [minWidth, maxWidth, onResize]
  );

  return (
    <div
      className="w-px shrink-0 cursor-col-resize relative group"
      style={{ backgroundColor: "var(--border-subtle)" }}
      onMouseDown={handleMouseDown}
      role="separator"
      aria-orientation="vertical"
      aria-label="Resize panel"
    >
      {/* Wider hover target */}
      <div
        className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-[var(--accent-teal-500)] opacity-0 group-hover:opacity-30 transition-opacity"
      />
    </div>
  );
}
