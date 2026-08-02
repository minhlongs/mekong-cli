#!/usr/bin/env node
/**
 * ZuneF login port — non-interactive installer for Anthropic-compatible JWT.
 * Reads install token from env or stdin and caches JWT under ~/.claude/mekong/.zunef-jwt-cache.
 */
const fs = require("fs");
const os = require("os");
const path = require("path");

const CACHE = path.join(os.homedir(), ".claude", "mekong", ".zunef-jwt-cache");
const DEV = path.join(os.homedir(), ".claude", "mekong", "zunef-device-id");

function ensureDevice() {
  try {
    const existing = fs.readFileSync(DEV, "utf8").trim();
    if (existing && existing.length >= 8) return existing;
  } catch {}
  const id = require("crypto").randomUUID().replace(/-/g, "").toLowerCase();
  fs.mkdirSync(path.dirname(DEV), { recursive: true });
  fs.writeFileSync(DEV, id, "utf8");
  return id;
}

async function main() {
  const token = process.argv[2] || process.env.ZUNEF_INSTALL_TOKEN || (() => {
    process.stderr.write("Provide ZuneF install token as arg or env ZUNEF_INSTALL_TOKEN.\n");
    process.exit(1);
    return "";
  })();

  const deviceId = ensureDevice();
  const url = `https://claude.zunef.com/api/claude-code/${token}/auth?deviceId=${encodeURIComponent(deviceId)}`;

  let jwt = null;
  for (let i = 1; i <= 3; i++) {
    try {
      const res = await fetch(url, {
        headers: {
          Accept: "text/plain",
          "X-ZUNEF-CLIENT": "mekong-cli",
          "X-Device-Id": deviceId,
        },
        signal: AbortSignal.timeout(8000),
      });
      const txt = (await res.text()).trim();
      if (!res.ok || txt.includes("<!DOCTYPE") || txt.includes("<html")) {
        throw new Error(`HTTP ${res.status}: ${txt.slice(0, 80)}`);
      }
      if (!txt) throw new Error("Empty token response");
      jwt = txt;
      break;
    } catch (e) {
      if (i === 3) {
        process.stderr.write(`ZuneF login failed after retries: ${e.message}
`);
        process.exit(1);
      }
      await new Promise((r) => setTimeout(r, i * 1000));
    }
  }

  fs.mkdirSync(path.dirname(CACHE), { recursive: true });
  fs.writeFileSync(
    CACHE,
    JSON.stringify({ jwt, ts: Date.now() }),
    "utf8"
  );

  process.stdout.write(jwt);
}

main();
