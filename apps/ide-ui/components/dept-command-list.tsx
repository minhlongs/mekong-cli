import { Terminal } from "lucide-react";
import { MD3Card } from "./md3-card";

export interface DeptCommand {
  slug: string;
  title: string;
  description: string;
  mcu: number;
}

interface DeptCommandListProps {
  commands: DeptCommand[];
}

export function DeptCommandList({ commands }: DeptCommandListProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {commands.map((cmd) => (
        <MD3Card key={cmd.slug} variant="outlined" className="flex flex-col gap-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div
                className="w-8 h-8 flex items-center justify-center rounded-[var(--md-sys-shape-corner-small)] flex-shrink-0"
                style={{ background: "var(--md-sys-color-primary-container)" }}
              >
                <Terminal
                  size={16}
                  style={{ color: "var(--md-sys-color-primary)" }}
                />
              </div>
              <code
                className="m3-label-large"
                style={{ color: "var(--md-sys-color-primary)" }}
              >
                /{cmd.slug}
              </code>
            </div>
            <span
              className="m3-label-medium px-2 py-0.5 rounded-[var(--md-sys-shape-corner-extra-small)] flex-shrink-0"
              style={{
                background: "var(--md-sys-color-surface-container-high)",
                color: "var(--md-sys-color-on-surface-variant)",
              }}
            >
              {cmd.mcu} MCU
            </span>
          </div>
          <p
            className="m3-title-medium"
            style={{ color: "var(--md-sys-color-on-surface)" }}
          >
            {cmd.title}
          </p>
          <p
            className="m3-body-medium"
            style={{ color: "var(--md-sys-color-on-surface-variant)" }}
          >
            {cmd.description}
          </p>
        </MD3Card>
      ))}
    </div>
  );
}
