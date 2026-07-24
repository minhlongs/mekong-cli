import { spawn } from "node:child_process";

export type MekongLoginOptions = {
  port: string;
  email?: string;
  token?: string;
  model?: string;
};

export async function login(opts: MekongLoginOptions) {
  if (!opts.port) {
    throw new Error("Missing --port. Use: claudeai|console|bedrock_vertex_foundry|zunef|local_m1_max");
  }
  switch (opts.port) {
    case "claudeai":
    case "console":
      return runClaudeAuth(opts.port, opts.email);
    case "bedrock_vertex_foundry":
      return runClaudeAuth("sso", opts.email);
    case "zunef":
      return runZunefLogin(opts.token);
    case "local_m1_max":
      return runLocalModel(opts.model);
    default:
      throw new Error(`Unknown port: ${opts.port}`);
  }
}

function runClaudeAuth(flag: string, email?: string) {
  const args = ["--" + flag];
  if (email) args.push("--email", email);
  const code = runSync("claude", ["auth", "login", ...args]);
  return { port: flag, status: code === 0 ? "ok" : "failed", code };
}

function runZunefLogin(token?: string) {
  const installToken = token ?? sanitizeEnv("ZUNEF_INSTALL_TOKEN");
  if (!installToken) throw new Error("Missing ZUNEF_INSTALL_TOKEN");
  const script = resolveRepoPath("mekong/scripts/zunef-login.py");
  const code = runSync(process.execPath, [script, installToken], { stdio: "inherit" });
  return { port: "zunef", status: code === 0 ? "ok" : "failed", code };
}

function runLocalModel(model?: string) {
  const script = resolveRepoPath("mekong/auth/local_model.py");
  const code = runSync(process.execPath, [script], { stdio: "inherit" });
  return { port: "local_m1_max", status: code === 0 ? "ok" : "failed", code, model: model ?? "local-llm" };
}

function runSync(cmd: string, args: string[], opts?: Record<string, unknown>) {
  const r = spawnSync(cmd, args, opts);
  if ("status" in r && typeof (r as { status?: number | null }).status === "number") return (r as { status: number }).status;
  return 1;
}

function sanitizeEnv(name: string) {
  return process.env[name] ?? "";
}

function resolveRepoPath(rel: string) {
  const base = process.cwd();
  const candidates = [
    rel,
    ["mekong-cli", rel],
    ["mekong", rel],
  ].map((p) => {
    const parts = Array.isArray(p) ? p : [p];
    return join(...[base, ...parts]);
  });
  for (const p of candidates) {
    if (exists(p)) return p;
  }
  return join(base, rel);
}

function join(...parts: string[]) {
  return parts.join("/");
}

type SpawnOpts = { stdio?: "inherit" | "pipe"; env?: Record<string, string> };
function spawnSync(
  cmd: string,
  args: string[],
  opts: SpawnOpts = { stdio: "ignore" }
): { status: number; stdout?: string; stderr?: string } {
  const cp = spawn(cmd, args, {
    shell: false,
    env: { ...process.env, ...(opts.env ?? {}) },
    stdio: opts.stdio ?? "ignore",
  });
  return new Promise<{ status: number; stdout: string; stderr: string }>((resolve) => {
    const chunks: Buffer[] = [];
    const errs: Buffer[] = [];
    if (cp.stdout && cp.stdout.on) cp.stdout.on("data", (d: Buffer) => chunks.push(d));
    if (cp.stderr && cp.stderr.on) cp.stderr.on("data", (d: Buffer) => errs.push(d));
    cp.on("close", (code) =>
      resolve({
        status: typeof code === "number" ? code : 1,
        stdout: Buffer.concat(chunks).toString("utf8"),
        stderr: Buffer.concat(errs).toString("utf8"),
      })
    );
    cp.on("error", () => resolve({ status: 1, stdout: "", stderr: "" }));
  }) as Promise<{ status: number; stdout: string; stderr: string }>;
}
