"use client";
/**
 * EngineControls — Start / Stop / Restart buttons.
 * Disabled states based on current engine status.
 */
import { Button } from "@/components/ds";
import type { EngineStatus } from "@/lib/types/engine-types";

interface EngineControlsProps {
  engineId: string;
  status: EngineStatus;
  onStart: (id: string) => void;
  onStop:  (id: string) => void;
  onRestart: (id: string) => void;
}

export function EngineControls({
  engineId,
  status,
  onStart,
  onStop,
  onRestart,
}: EngineControlsProps) {
  const isRunning = status === "running";
  const isStopped = status === "stopped";
  const isError   = status === "error";

  return (
    <div style={{ display: "flex", gap: "0.375rem", marginTop: "0.75rem" }}>
      <Button
        variant="primary"
        size="sm"
        disabled={isRunning || status === "idle"}
        onClick={() => onStart(engineId)}
      >
        Start
      </Button>
      <Button
        variant="danger"
        size="sm"
        disabled={isStopped}
        onClick={() => onStop(engineId)}
      >
        Stop
      </Button>
      <Button
        variant="secondary"
        size="sm"
        disabled={isStopped && !isError}
        onClick={() => onRestart(engineId)}
      >
        Restart
      </Button>
    </div>
  );
}
