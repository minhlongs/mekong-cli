import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export type MekongLoginOptions = {
  port: string;
  email?: string;
  token?: string;
  model?: string;
};

export async function login(opts: MekongLoginOptions) {
  const port = normalizePort(opts.port);
  if (!port) {
    throw new Error(
      "Missing --port. Use: claudeai|console|bedrock_vertex_foundry|zunef|local_m1_max"
    );
  }
  switch (port) {
    case "claudeai":
    case "console":
      return runClaudeAuth(port, opts.email);
    case "bedrock_vertex_foundry":
      return runClaudeAuth("sso", opts.email);
    case "zunef":
      return runZunefLogin(opts.token);
    case "local_m1_max":
      return runLocalModel(opts.model);
    default:
      throw new Error(`Unknown port: ${port}`);
  }
}

function normalizePort(value: string | undefined) {
  if (!value) return "";
  return value.trim().toLowerCase();
}

function runClaudeAuth(flag: string, email?: string) {
  const args: string[] = ["--" + flag];
  if (email) {
    args.push("--email", email);
  }
  const result = runCli(["claude", "auth", "login", ...args]);
  return {
    port: flag,
    status: result.status === 0 ? "ok" : "failed",
    code: result.status,
    stderr: result.stderr,
  };
}

function runZunefLogin(providedToken?: string) {
  const installToken = providedToken ?? sanitizeEnv("ZUNEF_INSTALL_TOKEN");
  if (!installToken) {
    throw new Error("Missing ZUNEF_INSTALL_TOKEN");
  }
  const script = resolveRepoPath(
    "mekong",
    "scripts",
    "zunef-login.py"
  );
  if (!fs.existsSync(script)) {
    throw new Error(`Missing ZuneF login script at ${script}`);
  }
  const result = runCli([process.execPath, script, installToken], {
    stdio: "inherit",
  });
  return {
    port: "zunef",
    status: result.status === 0 ? "ok" : "failed",
    code: result.status,
  };
}

function runLocalModel(model?: string) {
  const script = resolveRepoPath("mekong", "auth", "local_model.py");
  if (!fs.existsSync(script)) {
    throw new Error(`Missing local model script at ${script}`);
  }
  const result = runCli([process.execPath, script], {
    stdio: "inherit",
  });
  return {
    port: "local_m1_max",
    status: result.status === 0 ? "ok" : "failed",
    code: result.status,
    model: model ?? "local-llm",
  };
}

function runCli(
  args: string[],
  opts: { stdio?: "inherit" | "pipe" } = {}
) {
  const defaulted = {
    shell: false,
    env: { ...process.env },
    stdio: opts.stdio ?? "ignore",
  };
  return spawnSync(args[0], args.slice(1), defaulted);
}

function sanitizeEnv(name: string) {
  return process.env[name] ?? "";
}

function resolveRepoPath(...parts: string[]) {
  const base = process.cwd();
  const candidates = [
    path.join(base, ...parts),
    path.join(base, "mekong-cli", ...parts),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  return path.join(base, ...parts);
}
