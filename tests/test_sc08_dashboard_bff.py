"""Supreme Command #08 — Phase 3 Multi-Tenant Server-Side BFF & Zero Client Secret Suite.

Executes real TypeScript modules (`opc-bff-auth.ts`, `opc-cockpit-data.ts`, `agentops-api.ts`,
and all 5 Next.js Route Handlers under `apps/dashboard/app/api/opc/pilot-a/**`) inside Node
against an ephemeral localhost HTTP server, plus static bundle/source secret audits.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "apps" / "dashboard"

SCANNED_DASHBOARD_SUFFIXES = (".ts", ".tsx", ".js", ".mjs", ".json")


def _node_bin() -> str:
    node = shutil.which("node")
    assert node is not None, "Node.js binary is required to verify TypeScript BFF modules"
    return node


def _node_ts_args() -> list[str]:
    node = _node_bin()
    ver_proc = subprocess.run(
        [node, "-p", "process.versions.node.split('.')[0]"],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    major = int(ver_proc.stdout.strip())
    if major >= 24:
        return [node, "--no-warnings"]
    return [node, "--no-warnings", "--experimental-strip-types"]


def _run_node_harness(script_body: str, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    loader_code = f"""
import {{ registerHooks }} from 'node:module';
import {{ pathToFileURL }} from 'node:url';
import fs from 'node:fs';
import path from 'node:path';

const DASHBOARD_ROOT = {json.dumps(str(DASHBOARD_DIR))};

function resolveTsCandidate(basePath) {{
  const candidates = [
    basePath,
    `${{basePath}}.ts`,
    `${{basePath}}.tsx`,
    path.join(basePath, 'index.ts'),
  ];
  for (const candidate of candidates) {{
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {{
      return pathToFileURL(candidate).href;
    }}
  }}
  return null;
}}

registerHooks({{
  resolve(specifier, context, nextResolve) {{
    if (specifier.startsWith('@/')) {{
      const resolved = resolveTsCandidate(path.join(DASHBOARD_ROOT, specifier.slice(2)));
      if (resolved) {{
        return {{ url: resolved, shortCircuit: true }};
      }}
    }}
    if ((specifier.startsWith('./') || specifier.startsWith('../')) && context.parentURL?.startsWith('file:')) {{
      const parentDir = path.dirname(new URL(context.parentURL).pathname);
      const resolved = resolveTsCandidate(path.resolve(parentDir, specifier));
      if (resolved) {{
        return {{ url: resolved, shortCircuit: true }};
      }}
    }}
    return nextResolve(specifier, context);
  }}
}});
"""
    loader_data_url = "data:text/javascript;base64," + base64.b64encode(
        loader_code.encode("utf-8")
    ).decode("ascii")

    env = dict(os.environ)
    for k in list(env.keys()):
        if k.startswith("MEKONG_") or k.startswith("NEXT_PUBLIC_MEKONG"):
            env.pop(k, None)
    if extra_env:
        env.update(extra_env)

    proc = subprocess.run(
        [*_node_ts_args(), "--import", loader_data_url, "--input-type=module", "-e", script_body],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, (
        f"Node BFF harness failed (rc={proc.returncode}):\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    assert lines, f"Expected JSON output from Node harness, stderr={proc.stderr}"
    parsed = json.loads(lines[-1])
    assert isinstance(parsed, dict)
    return parsed


def _iter_dashboard_source_files() -> list[Path]:
    collected: list[Path] = []
    for root, dirs, files in os.walk(DASHBOARD_DIR):
        dirs[:] = [d for d in dirs if d not in {"node_modules", ".next", ".turbo", ".vercel"}]
        root_path = Path(root)
        for filename in files:
            if filename.endswith(SCANNED_DASHBOARD_SUFFIXES) or filename.startswith(".env"):
                collected.append(root_path / filename)
    return collected


def test_static_source_and_env_secret_audit() -> None:
    files = _iter_dashboard_source_files()
    assert files, "Expected dashboard source files"

    forbidden_literals = (
        "NEXT_PUBLIC_MEKONG_TENANT_API_KEY",
        "NEXT_PUBLIC_MEKONG_API_KEY",
        "NEXT_PUBLIC_MEKONG_API_URL",
        "NEXT_PUBLIC_MEKONG_TENANT_ID",
        "0xdeadbeef",
        "0x41c6ce57",
        "offline_webcrypto",
    )

    violations: list[str] = []
    for file_path in files:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        rel = file_path.relative_to(REPO_ROOT)
        for token in forbidden_literals:
            if token in text:
                violations.append(f"{rel}: contains forbidden token '{token}'")

    assert not violations, "Dashboard client-secret / pseudo-crypto violations:\n" + "\n".join(violations)

    # Strict TypeScript & no-console audit across all OPC + BFF files
    strict_targets = [
        DASHBOARD_DIR / "lib" / "opc-bff-auth.ts",
        DASHBOARD_DIR / "lib" / "opc-cockpit-data.ts",
        DASHBOARD_DIR / "app" / "dashboard" / "opc" / "page.tsx",
        *sorted((DASHBOARD_DIR / "app" / "api" / "opc" / "pilot-a").rglob("*.ts")),
    ]
    assert len(strict_targets) == 8, f"Expected 8 OPC/BFF target files, found {len(strict_targets)}"

    any_pattern = re.compile(r"(:\s*any\b|\bas\s+any\b)")
    console_pattern = re.compile(r"\bconsole\.(log|warn|error|info|debug)\b")
    for target in strict_targets:
        content = target.read_text(encoding="utf-8")
        rel = target.relative_to(REPO_ROOT)
        assert not any_pattern.search(content), f"Forbidden 'any' type in {rel}"
        assert not console_pattern.search(content), f"Forbidden console statement in {rel}"

    env_example = (DASHBOARD_DIR / ".env.local.example").read_text(encoding="utf-8")
    for required_var in (
        "MEKONG_DASHBOARD_SESSION_SECRET=",
        "MEKONG_TENANT_KEYS_JSON=",
        "MEKONG_GATEWAY_INTERNAL_URL=",
    ):
        assert required_var in env_example, f"Missing {required_var} in .env.local.example"
    assert "NEXT_PUBLIC_MEKONG" not in env_example

    checkout_demo = (DASHBOARD_DIR / "app" / "checkout" / "demo" / "page.tsx").read_text(encoding="utf-8")
    assert "checkoutSession.checkout_secret" in checkout_demo
    assert "localStorage.setItem('RAAS_LICENSE_KEY'" not in checkout_demo
    assert 'localStorage.setItem("RAAS_LICENSE_KEY"' not in checkout_demo

    # If a Next.js production build is present, verify zero secret leakage in static client chunks
    static_chunks_dir = DASHBOARD_DIR / (".ne" + "xt") / "static"
    if static_chunks_dir.is_dir():
        chunk_files = [p for p in static_chunks_dir.rglob("*") if p.is_file()]
        assert chunk_files, "Expected compiled static chunks when build output exists"
        for chunk in chunk_files:
            chunk_text = chunk.read_text(encoding="utf-8", errors="replace")
            for forbidden_chunk_token in (
                *forbidden_literals,
                "mk_opc_",
                "MEKONG_DASHBOARD_SESSION_SECRET",
                "MEKONG_DASHBOARD_OWNER_LOGIN_TOKEN",
                "MEKONG_TENANT_KEYS_JSON",
                "canary_session_secret",
                "canary_owner_bootstrap",
            ):
                assert forbidden_chunk_token not in chunk_text, (
                    f"Client bundle leak '{forbidden_chunk_token}' in {chunk.relative_to(REPO_ROOT)}"
                )


def test_missing_session_secret_fails_closed_503() -> None:
    script = """
import { GET as sessionGet, POST as sessionPost } from './apps/dashboard/app/api/opc/pilot-a/session/route.ts';
import { POST as webhookPost } from './apps/dashboard/app/api/opc/pilot-a/webhook/zalo/route.ts';
import { POST as decidePost } from './apps/dashboard/app/api/opc/pilot-a/decide/route.ts';
import { GET as runGet } from './apps/dashboard/app/api/opc/pilot-a/runs/[runId]/route.ts';
import { GET as exportGet } from './apps/dashboard/app/api/opc/pilot-a/draft-export/[runId]/route.ts';

let upstreamCalls = 0;
globalThis.fetch = async () => {
  upstreamCalls += 1;
  return new Response('{}', { status: 200 });
};

const r1 = await sessionGet(new Request('http://localhost:3000/api/opc/pilot-a/session'));
const r2 = await sessionPost(new Request('http://localhost:3000/api/opc/pilot-a/session', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000' },
  body: JSON.stringify({ credential: 'some-long-bootstrap-token-123456', tenant_id: 'tenant_alpha' }),
}));
const r3 = await webhookPost(new Request('http://localhost:3000/api/opc/pilot-a/webhook/zalo', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000' },
  body: JSON.stringify({
    tenant_id: 'tenant_alpha',
    event_id: 'ev_1',
    sender_id: 'u_1',
    sender_name: 'Client',
    message_text: 'Xin bao gia',
  }),
}));
const r4 = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000' },
  body: JSON.stringify({
    tenant_id: 'tenant_alpha',
    run_id: 'run_123',
    decision: 'approve',
    action_digest: 'a'.repeat(64),
  }),
}));
const r5 = await runGet(
  new Request('http://localhost:3000/api/opc/pilot-a/runs/run_123?tenant_id=tenant_alpha'),
  { params: Promise.resolve({ runId: 'run_123' }) }
);
const r6 = await exportGet(
  new Request('http://localhost:3000/api/opc/pilot-a/draft-export/run_123?tenant_id=tenant_alpha'),
  { params: Promise.resolve({ runId: 'run_123' }) }
);

const statuses = [r1.status, r2.status, r3.status, r4.status, r5.status, r6.status];
const bodies = await Promise.all([r1.json(), r2.json(), r3.json(), r4.json(), r5.json(), r6.json()]);
process.stdout.write(JSON.stringify({ statuses, errors: bodies.map((b) => b.error), upstreamCalls }) + '\\n');
"""
    for bad_secret in ("", "short-secret-under-32-chars"):
        result = _run_node_harness(script, {"MEKONG_DASHBOARD_SESSION_SECRET": bad_secret})
        assert result["statuses"] == [503, 503, 503, 503, 503, 503]
        assert all(err == "bff_session_secret_unconfigured" for err in result["errors"])
        assert result["upstreamCalls"] == 0


def test_missing_forged_and_expired_session_cookies_rejected_401() -> None:
    script = """
import { createHmac } from 'node:crypto';
import { issueOpcBffSessionToken } from './apps/dashboard/lib/opc-bff-auth.ts';
import { GET as sessionGet } from './apps/dashboard/app/api/opc/pilot-a/session/route.ts';
import { POST as webhookPost } from './apps/dashboard/app/api/opc/pilot-a/webhook/zalo/route.ts';
import { POST as decidePost } from './apps/dashboard/app/api/opc/pilot-a/decide/route.ts';
import { GET as runGet } from './apps/dashboard/app/api/opc/pilot-a/runs/[runId]/route.ts';
import { GET as exportGet } from './apps/dashboard/app/api/opc/pilot-a/draft-export/[runId]/route.ts';

let upstreamCalls = 0;
globalThis.fetch = async () => {
  upstreamCalls += 1;
  return new Response('{}', { status: 200 });
};

const validIssued = issueOpcBffSessionToken({
  sub: 'owner_alpha',
  workspaceId: 'ws_alpha',
  allowedTenants: ['tenant_alpha'],
  role: 'viewer',
});
if (!validIssued.ok) throw new Error('Failed to issue test token');

const parts = validIssued.token.split('.');
const forgedSigCookie = `mk_opc_session=v1.${parts[1]}.${'f'.repeat(64)}`;

const escalatedPayload = Buffer.from(JSON.stringify({
  sub: 'owner_alpha',
  workspaceId: 'ws_alpha',
  allowedTenants: ['tenant_alpha'],
  role: 'owner',
  iat: Math.floor(Date.now() / 1000) - 60,
  exp: Math.floor(Date.now() / 1000) + 3600,
})).toString('base64url');
const tamperedPayloadCookie = `mk_opc_session=v1.${escalatedPayload}.${parts[2]}`;

const nowSec = Math.floor(Date.now() / 1000);
const expiredPayload = Buffer.from(JSON.stringify({
  sub: 'owner_alpha',
  workspaceId: 'ws_alpha',
  allowedTenants: ['tenant_alpha'],
  role: 'owner',
  iat: nowSec - 7200,
  exp: nowSec - 10,
})).toString('base64url');
const expiredMac = createHmac('sha256', process.env.MEKONG_DASHBOARD_SESSION_SECRET)
  .update(`v1.${expiredPayload}`, 'utf8')
  .digest('hex');
const expiredCookie = `mk_opc_session=v1.${expiredPayload}.${expiredMac}`;

const allStatuses = [];
for (const cookieHeader of ['', forgedSigCookie, tamperedPayloadCookie, expiredCookie]) {
  const headers = {
    'Content-Type': 'application/json',
    Origin: 'http://localhost:3000',
    ...(cookieHeader ? { Cookie: cookieHeader } : {}),
  };
  const s1 = (await sessionGet(new Request('http://localhost:3000/api/opc/pilot-a/session', { headers }))).status;
  const s2 = (await webhookPost(new Request('http://localhost:3000/api/opc/pilot-a/webhook/zalo', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      event_id: 'ev_1',
      sender_id: 'u_1',
      sender_name: 'Client',
      message_text: 'Xin bao gia',
    }),
  }))).status;
  const s3 = (await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      run_id: 'run_123',
      decision: 'approve',
      action_digest: 'a'.repeat(64),
    }),
  }))).status;
  const s4 = (await runGet(
    new Request('http://localhost:3000/api/opc/pilot-a/runs/run_123?tenant_id=tenant_alpha', { headers }),
    { params: Promise.resolve({ runId: 'run_123' }) }
  )).status;
  const s5 = (await exportGet(
    new Request('http://localhost:3000/api/opc/pilot-a/draft-export/run_123?tenant_id=tenant_alpha', { headers }),
    { params: Promise.resolve({ runId: 'run_123' }) }
  )).status;
  allStatuses.push([s1, s2, s3, s4, s5]);
}

process.stdout.write(JSON.stringify({ allStatuses, upstreamCalls }) + '\\n');
"""
    result = _run_node_harness(
        script,
        {
            "MEKONG_DASHBOARD_SESSION_SECRET": "s" * 48,
            "MEKONG_TENANT_KEYS_JSON": json.dumps({"tenant_alpha": "mk_opc_alpha_secret_12345"}),
        },
    )
    assert result["upstreamCalls"] == 0
    for row in result["allStatuses"]:
        assert row == [401, 401, 401, 401, 401]


def test_cross_tenant_isolation_and_csrf_and_role_gates() -> None:
    script = """
import http from 'node:http';
import { issueOpcBffSessionToken } from './apps/dashboard/lib/opc-bff-auth.ts';
import { POST as sessionPost, DELETE as sessionDelete } from './apps/dashboard/app/api/opc/pilot-a/session/route.ts';
import { POST as webhookPost } from './apps/dashboard/app/api/opc/pilot-a/webhook/zalo/route.ts';
import { POST as decidePost } from './apps/dashboard/app/api/opc/pilot-a/decide/route.ts';
import { GET as runGet } from './apps/dashboard/app/api/opc/pilot-a/runs/[runId]/route.ts';
import { GET as exportGet } from './apps/dashboard/app/api/opc/pilot-a/draft-export/[runId]/route.ts';

const upstreamLog = [];
const server = http.createServer((req, res) => {
  let raw = '';
  req.on('data', (chunk) => { raw += chunk; });
  req.on('end', () => {
    upstreamLog.push({
      method: req.method,
      url: req.url,
      apiKey: req.headers['x-api-key'],
      body: raw ? JSON.parse(raw) : null,
    });
    if (req.url?.startsWith('/v1/opc/pilot-a/draft-export/')) {
      res.writeHead(200, { 'Content-Type': 'text/csv; charset=utf-8' });
      res.end('invoice_status,run_id,leak_probe\\nDRAFT_PENDING_TVAN,run_123,mk_opc_alpha_secret_999');
      return;
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'INTERRUPT_AUTHORIZE',
      run_id: 'run_123',
      tenant_id: 'tenant_alpha',
      action_digest: 'b'.repeat(64),
      card_sig: 'deadbeefcafebabe'.repeat(4),
      card_url: '/v1/opc/pilot-a/card/run_123?tenant_id=tenant_alpha&sig=' + 'c'.repeat(64),
      notification_cards: {
        zalo_url: 'https://example.test/v1/opc/pilot-a/card/run_123?sig=' + 'c'.repeat(64) + '&tenant_id=tenant_alpha',
      },
      debug_note: 'upstream_key=mk_opc_alpha_secret_999',
    }));
  });
});

await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const addr = server.address();
const port = typeof addr === 'object' && addr ? addr.port : 0;
process.env.MEKONG_GATEWAY_INTERNAL_URL = `http://127.0.0.1:${port}`;

try {
  const makeCookie = (role, workspaceId = 'ws_alpha', allowedTenants = ['tenant_alpha']) => {
    const issued = issueOpcBffSessionToken({ sub: `u_${role}`, workspaceId, allowedTenants, role });
    if (!issued.ok) throw new Error('issue failed');
    return `mk_opc_session=${issued.token}`;
  };

  const ownerAlphaCookie = makeCookie('owner', 'ws_alpha', ['tenant_alpha']);
  const operatorAlphaCookie = makeCookie('operator', 'ws_alpha', ['tenant_alpha']);
  const viewerAlphaCookie = makeCookie('viewer', 'ws_alpha', ['tenant_alpha']);
  // Token claiming tenant_bravo inside ws_alpha, which server MEKONG_WORKSPACE_TENANTS_JSON forbids:
  const overclaimingCookie = makeCookie('owner', 'ws_alpha', ['tenant_alpha', 'tenant_bravo']);

  // 1. Cross-tenant isolation (ws_alpha -> tenant_bravo) across all 4 tenant routes
  const ct1 = await webhookPost(new Request('http://localhost:3000/api/opc/pilot-a/webhook/zalo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: ownerAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_bravo',
      event_id: 'ev_ct',
      sender_id: 's_1',
      sender_name: 'Client',
      message_text: 'Bao gia',
    }),
  }));
  const ct2 = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: ownerAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_bravo',
      run_id: 'run_123',
      decision: 'approve',
      action_digest: 'b'.repeat(64),
    }),
  }));
  const ct3 = await runGet(
    new Request('http://localhost:3000/api/opc/pilot-a/runs/run_123?tenant_id=tenant_bravo', {
      headers: { Cookie: ownerAlphaCookie },
    }),
    { params: Promise.resolve({ runId: 'run_123' }) }
  );
  const ct4 = await exportGet(
    new Request('http://localhost:3000/api/opc/pilot-a/draft-export/run_123?tenant_id=tenant_bravo&fmt=csv', {
      headers: { Cookie: ownerAlphaCookie },
    }),
    { params: Promise.resolve({ runId: 'run_123' }) }
  );
  const ct5 = await runGet(
    new Request('http://localhost:3000/api/opc/pilot-a/runs/run_123?tenant_id=tenant_bravo', {
      headers: { Cookie: overclaimingCookie },
    }),
    { params: Promise.resolve({ runId: 'run_123' }) }
  );
  const crossTenantErrors = await Promise.all([ct1.json(), ct2.json(), ct3.json(), ct4.json(), ct5.json()]);
  const crossTenantUpstreamCalls = upstreamLog.length;

  // 2. Cross-origin CSRF attempts on mutating routes -> 403 with 0 upstream calls
  const csrfDecide = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Origin: 'https://evil.example',
      Cookie: ownerAlphaCookie,
    },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      run_id: 'run_123',
      decision: 'approve',
      action_digest: 'b'.repeat(64),
    }),
  }));
  const csrfFetchSite = await webhookPost(new Request('http://localhost:3000/api/opc/pilot-a/webhook/zalo', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Sec-Fetch-Site': 'cross-site',
      Cookie: ownerAlphaCookie,
    },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      event_id: 'ev_csrf',
      sender_id: 's_1',
      sender_name: 'Client',
      message_text: 'Bao gia',
    }),
  }));
  const csrfLogout = await sessionDelete(new Request('http://localhost:3000/api/opc/pilot-a/session', {
    method: 'DELETE',
    headers: { Origin: 'https://evil.example', Cookie: ownerAlphaCookie },
  }));
  const csrfUpstreamCalls = upstreamLog.length;

  // 3. Role enforcement: viewer, operator, owner
  const viewerDecide = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: viewerAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      run_id: 'run_123',
      decision: 'handoff',
      action_digest: 'b'.repeat(64),
    }),
  }));
  const operatorApprove = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: operatorAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      run_id: 'run_123',
      decision: 'approve',
      action_digest: 'b'.repeat(64),
    }),
  }));
  const blockedRoleUpstreamCalls = upstreamLog.length;

  const operatorHandoff = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: operatorAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      run_id: 'run_123',
      decision: 'handoff',
      action_digest: 'b'.repeat(64),
      revision_notes: 'Escalating to Zalo OA human chat',
    }),
  }));

  const operatorWebhook = await webhookPost(new Request('http://localhost:3000/api/opc/pilot-a/webhook/zalo', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: operatorAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      event_id: 'ev_ok_1',
      sender_id: '84909382910',
      sender_name: 'Minh Long',
      message_text: 'Can bao gia Zalo OA',
      grant_consent: true,
      service_rates_vnd: { zalo_oa_lead_to_quote: 1 },
    }),
  }));
  const webhookJsonText = await operatorWebhook.text();

  const ownerApprove = await decidePost(new Request('http://localhost:3000/api/opc/pilot-a/decide', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000', Cookie: ownerAlphaCookie },
    body: JSON.stringify({
      tenant_id: 'tenant_alpha',
      run_id: 'run_123',
      decision: 'approve',
      action_digest: 'b'.repeat(64),
    }),
  }));

  const viewerExport = await exportGet(
    new Request('http://localhost:3000/api/opc/pilot-a/draft-export/run_123?tenant_id=tenant_alpha&fmt=csv&vat_rate_pct=8&target_provider=misa_meinvoice', {
      headers: { Cookie: viewerAlphaCookie },
    }),
    { params: Promise.resolve({ runId: 'run_123' }) }
  );
  const exportText = await viewerExport.text();

  // 4. Session login & logout Set-Cookie attributes
  const loginRes = await sessionPost(new Request('http://localhost:3000/api/opc/pilot-a/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'http://localhost:3000' },
    body: JSON.stringify({
      credential: 'bootstrap_owner_token_alpha_123456',
      workspace_id: 'ws_alpha',
      tenant_id: 'tenant_alpha',
    }),
  }));
  const loginSetCookie = loginRes.headers.get('set-cookie') || '';
  const loginBodyText = await loginRes.text();

  process.stdout.write(JSON.stringify({
    crossTenantStatuses: [ct1.status, ct2.status, ct3.status, ct4.status, ct5.status],
    crossTenantCodes: crossTenantErrors.map((e) => e.error),
    crossTenantUpstreamCalls,
    csrfStatuses: [csrfDecide.status, csrfFetchSite.status, csrfLogout.status],
    csrfUpstreamCalls,
    roleStatuses: {
      viewerDecide: viewerDecide.status,
      operatorApprove: operatorApprove.status,
      operatorHandoff: operatorHandoff.status,
      operatorWebhook: operatorWebhook.status,
      ownerApprove: ownerApprove.status,
      viewerExport: viewerExport.status,
    },
    blockedRoleUpstreamCalls,
    upstreamLog,
    webhookJsonText,
    webhookHeaders: {
      cacheControl: operatorWebhook.headers.get('cache-control'),
      referrerPolicy: operatorWebhook.headers.get('referrer-policy'),
    },
    exportText,
    exportHeaders: {
      cacheControl: viewerExport.headers.get('cache-control'),
      referrerPolicy: viewerExport.headers.get('referrer-policy'),
      contentType: viewerExport.headers.get('content-type'),
    },
    loginStatus: loginRes.status,
    loginSetCookie,
    loginBodyText,
  }) + '\\n');
} finally {
  server.close();
}
"""
    res = _run_node_harness(
        script,
        {
            "MEKONG_DASHBOARD_SESSION_SECRET": "k" * 48,
            "MEKONG_DASHBOARD_OWNER_LOGIN_TOKEN": "bootstrap_owner_token_alpha_123456",
            "MEKONG_WORKSPACE_TENANTS_JSON": json.dumps(
                {"ws_alpha": ["tenant_alpha"], "ws_bravo": ["tenant_bravo"]}
            ),
            "MEKONG_TENANT_KEYS_JSON": json.dumps(
                {
                    "tenant_alpha": "mk_opc_alpha_secret_999",
                    "tenant_bravo": "mk_opc_bravo_secret_888",
                }
            ),
        },
    )

    # Cross-tenant assertions
    assert res["crossTenantStatuses"] == [403, 403, 403, 403, 403]
    assert all(code == "cross_tenant_forbidden" for code in res["crossTenantCodes"])
    assert res["crossTenantUpstreamCalls"] == 0

    # CSRF assertions
    assert res["csrfStatuses"] == [403, 403, 403]
    assert res["csrfUpstreamCalls"] == 0

    # Role assertions
    assert res["blockedRoleUpstreamCalls"] == 0
    assert res["roleStatuses"] == {
        "viewerDecide": 403,
        "operatorApprove": 403,
        "operatorHandoff": 200,
        "operatorWebhook": 200,
        "ownerApprove": 200,
        "viewerExport": 200,
    }

    # Upstream calls inspection: server-only X-API-Key injected, grant_consent forced false, operator service_rates_vnd stripped
    upstream_log = res["upstreamLog"]
    assert len(upstream_log) == 4
    for entry in upstream_log:
        assert entry["apiKey"] == "mk_opc_alpha_secret_999"
    webhook_call = upstream_log[1]
    assert webhook_call["url"] == "/v1/opc/pilot-a/webhook/zalo"
    assert webhook_call["body"]["tenant_id"] == "tenant_alpha"
    assert webhook_call["body"]["grant_consent"] is False
    assert "service_rates_vnd" not in webhook_call["body"]

    # Secret & capability token scrubbing on BFF responses
    webhook_body_str = res["webhookJsonText"]
    assert "mk_opc_" not in webhook_body_str
    assert "card_sig" not in webhook_body_str
    assert "sig=" not in webhook_body_str
    assert "no-store" in (res["webhookHeaders"]["cacheControl"] or "")
    assert res["webhookHeaders"]["referrerPolicy"] == "no-referrer"

    export_body_str = res["exportText"]
    assert "DRAFT_PENDING_TVAN" in export_body_str
    assert "mk_opc_" not in export_body_str
    assert "no-store" in (res["exportHeaders"]["cacheControl"] or "")
    assert res["exportHeaders"]["referrerPolicy"] == "no-referrer"
    assert "text/csv" in (res["exportHeaders"]["contentType"] or "")

    # Session cookie attributes
    assert res["loginStatus"] == 200
    assert "mk_opc_session=v1." in res["loginSetCookie"]
    assert "HttpOnly" in res["loginSetCookie"]
    assert "SameSite=Strict" in res["loginSetCookie"]
    assert "Path=/api/opc/pilot-a" in res["loginSetCookie"]
    assert "mk_opc_" not in res["loginBodyText"]
    assert "bootstrap_owner_token" not in res["loginBodyText"]

    # Empty MEKONG_WORKSPACE_TENANTS_JSON={} treated as unconfigured (does not lock out login or tenant access)
    empty_ws = _run_node_harness(
        """
import { authenticateBffOwnerLogin, authorizeBffTenantRequest } from './apps/dashboard/lib/opc-bff-auth.ts';
const login = authenticateBffOwnerLogin({ credential: 'bootstrap_owner_token_alpha_123456', workspaceId: 'ws_default' });
const req = new Request('http://localhost:3000/api/opc/pilot-a/runs/r1?tenant_id=tenant_alpha', {
  headers: login.ok ? { cookie: login.cookieHeader.split(';')[0] } : {},
});
const authz = authorizeBffTenantRequest(req, 'tenant_alpha', 'viewer');
process.stdout.write(JSON.stringify({ loginOk: login.ok, authzOk: authz.ok }) + '\\n');
""",
        {
            "MEKONG_DASHBOARD_SESSION_SECRET": "k" * 48,
            "MEKONG_DASHBOARD_OWNER_LOGIN_TOKEN": "bootstrap_owner_token_alpha_123456",
            "MEKONG_WORKSPACE_TENANTS_JSON": "{}",
            "MEKONG_TENANT_KEYS_JSON": json.dumps({"tenant_alpha": "mk_opc_alpha_secret_999"}),
        },
    )
    assert empty_ws == {"loginOk": True, "authzOk": True}


@pytest.mark.parametrize("failure_status", [401, 403, 409, 502, 503])
def test_client_helpers_fail_closed_and_webcrypto_throws_without_subtle(failure_status: int) -> None:
    script = f"""
import {{ computeSha256Hex, syncPilotADecision, syncPilotAZaloWebhook }} from './apps/dashboard/lib/opc-cockpit-data.ts';
import {{ getCheckoutStatus }} from './apps/dashboard/lib/agentops-api.ts';
const validHash = await computeSha256Hex('abc');
const origDesc = Object.getOwnPropertyDescriptor(globalThis, 'crypto');
Object.defineProperty(globalThis, 'crypto', {{ value: {{}}, configurable: true }});
let cryptoErrorMsg = '';
try {{ await computeSha256Hex('abc'); }} catch (err) {{ cryptoErrorMsg = err instanceof Error ? err.message : String(err); }}
finally {{ if (origDesc) Object.defineProperty(globalThis, 'crypto', origDesc); }}
const capturedCalls = [];
globalThis.fetch = async (input, init) => {{
  capturedCalls.push({{ url: String(input), headers: init?.headers || {{}}, credentials: init?.credentials }});
  if (String(input).includes('/v1/checkout/status')) {{
    return new Response(JSON.stringify({{
      order_id: 'mk-123456',
      status: 'paid',
      tier: 'PREMIUM',
      license_key: 'MEKONG-RAAS-v1.payload.sig',
      tenant_id: 'org_alpha',
    }}), {{ status: 200, headers: {{ 'Content-Type': 'application/json' }} }});
  }}
  return new Response(
    JSON.stringify({{ error: 'simulated_rejection', message: 'Rejected fail-closed' }}),
    {{ status: {failure_status}, headers: {{ 'Content-Type': 'application/json' }} }}
  );
}};

const webhookRes = await syncPilotAZaloWebhook({{
  tenantId: 'tenant_alpha',
  eventId: 'ev_1',
  senderName: 'Shop Client',
  senderContact: 'zalo:84909000111',
  messageText: 'Xin bao gia',
  projectTitle: 'Pilot A',
  requestedServices: ['zalo_oa_lead_to_quote'],
  estimatedHours: 4,
  currency: 'VND',
  language: 'vi',
  extractionConfidence: 0.95,
}});

const decideRes = await syncPilotADecision({{
  tenantId: 'tenant_alpha',
  runId: 'run_123',
  decision: 'approve',
  actionDigest: validHash,
  revisionNotes: 'Approve test',
}});

const checkoutRes = await getCheckoutStatus('mk-123456', 'chk_secret_xyz_987');

process.stdout.write(JSON.stringify({{
  validHash,
  cryptoErrorMsg,
  webhookRes,
  decideRes,
  checkoutRes,
  capturedCalls,
}}) + '\\n');
"""
    res = _run_node_harness(script)
    assert res["validHash"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert "CRYPTO_UNAVAILABLE" in res["cryptoErrorMsg"]

    for sync_res in (res["webhookRes"], res["decideRes"]):
        assert sync_res["synced"] is False
        assert sync_res["failedClosed"] is True
        assert sync_res["serverRejected"] is True
        assert sync_res["mode"] == "failed_closed"
        assert sync_res["httpStatus"] == failure_status

    calls = res["capturedCalls"]
    assert calls[0]["url"] == "/api/opc/pilot-a/webhook/zalo"
    assert calls[0]["credentials"] == "same-origin"
    assert "X-API-Key" not in calls[0]["headers"]
    assert calls[1]["url"] == "/api/opc/pilot-a/decide"
    assert calls[1]["credentials"] == "same-origin"
    assert "X-API-Key" not in calls[1]["headers"]
    assert calls[2]["headers"]["X-Checkout-Secret"] == "chk_secret_xyz_987"
    assert res["checkoutRes"]["status"] == "paid"
