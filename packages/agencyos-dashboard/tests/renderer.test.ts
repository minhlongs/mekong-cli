import { describe, it, expect, beforeEach } from "vitest";
import { TerminalDashboard, DashboardData } from "../src/renderer.js";

const SAMPLE: DashboardData = {
  status: { uptime: 3665, version: "0.1.0", paneCount: 4, taskCount: 2 },
  panes: [
    { id: "pane-0", provider: "claude", state: "running", project: "mekong-cli" },
    { id: "pane-1", provider: "gemini", state: "idle", project: "agencyos" },
  ],
  tasks: [
    { id: "t1", name: "Implement auth", status: "active", assignedPane: "pane-0" },
    { id: "t2", name: "Write tests", status: "queued", assignedPane: "pane-1" },
  ],
  raas: { tenants: 3, revenue: 420, health: "healthy" },
  agiScore: { score: 42, capabilitiesCount: 4 },
};

describe("TerminalDashboard", () => {
  let td: TerminalDashboard;

  beforeEach(() => {
    td = new TerminalDashboard();
  });

  it("renderStatusBar contains version string", () => {
    const out = td.renderStatusBar(SAMPLE);
    expect(out).toContain("0.1.0");
  });

  it("renderStatusBar contains uptime in hours/minutes", () => {
    const out = td.renderStatusBar(SAMPLE);
    expect(out).toContain("1h");
  });

  it("renderPaneGrid uses box-drawing chars", () => {
    const out = td.renderPaneGrid(SAMPLE.panes);
    expect(out).toContain("┌");
    expect(out).toContain("┐");
    expect(out).toContain("└");
    expect(out).toContain("┘");
    expect(out).toContain("│");
  });

  it("renderPaneGrid shows pane ids", () => {
    const out = td.renderPaneGrid(SAMPLE.panes);
    expect(out).toContain("pane-0");
    expect(out).toContain("pane-1");
  });

  it("renderPaneGrid with empty panes shows fallback", () => {
    const out = td.renderPaneGrid([]);
    expect(out).toContain("No panes");
  });

  it("renderTaskList shows task names", () => {
    const out = td.renderTaskList(SAMPLE.tasks);
    expect(out).toContain("Implement auth");
    expect(out).toContain("Write tests");
  });

  it("renderTaskList with empty tasks shows fallback", () => {
    const out = td.renderTaskList([]);
    expect(out).toContain("No tasks");
  });

  it("renderFullDashboard contains all section headers", () => {
    const out = td.renderFullDashboard(SAMPLE);
    expect(out).toContain("Panes");
    expect(out).toContain("Tasks");
    expect(out).toContain("RaaS");
    expect(out).toContain("AGI Evolution");
  });

  it("renderCompactView is a single line", () => {
    const out = td.renderCompactView(SAMPLE);
    expect(out.includes("\n")).toBe(false);
  });

  it("renderCompactView shows running pane count", () => {
    const out = td.renderCompactView(SAMPLE);
    expect(out).toContain("1/2 running");
  });

  it("renderCompactView shows agi score", () => {
    const out = td.renderCompactView(SAMPLE);
    expect(out).toContain("agi:42");
  });
});
