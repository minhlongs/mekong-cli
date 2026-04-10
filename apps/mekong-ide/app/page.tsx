"use client";
import { useEffect } from "react";

// Root page — meta-redirect to /ide for static export compatibility
export default function RootPage() {
  useEffect(() => {
    window.location.replace("/ide");
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-primary)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--text-muted)",
      }}
    >
      Loading Mekong IDE...
    </div>
  );
}
