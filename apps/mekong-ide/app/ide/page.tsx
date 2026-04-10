"use client";

import dynamic from "next/dynamic";

const IdeShell = dynamic(
  () => import("@/components/layout").then((m) => m.IdeShell),
  { ssr: false, loading: () => <div style={{ background: "#0a0a0f", height: "100vh" }} /> }
);

export default function IdePage() {
  return <IdeShell />;
}
