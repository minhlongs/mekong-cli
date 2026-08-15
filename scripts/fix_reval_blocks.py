#!/usr/bin/env python3
"""Add re-validation blocks after SSRF checks in _execute_api_step and _execute_browse_step."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

reval_block = """        # Re-validate pinned IP immediately before request (defense-in-depth
        # against DNS rebinding: if DNS changed since validation, block it).
        if pinned_ip:
            _addr = ipaddress.ip_address(pinned_ip)
            for network in _SSRF_BLOCKED_NETWORKS:
                if _addr in network:
                    self.console.print(
                        f"[bold red]SECURITY:[/bold red] "
                        f"SSRF blocked - pinned IP {pinned_ip} in blocked range {network}"
                    )
                    return ExecutionResult(
                        exit_code=1,
                        stdout="",
                        stderr=f"SSRF blocked (pinned IP): {url}",
                        metadata={"mode": "api", "ssrf_blocked": True},
                    )

"""

# Insert after the SSRF early-return block in _execute_api_step
# Find line with `metadata={"mode": "api", "ssrf_blocked": True},` followed by `)` then empty then console.print
inserted_api = False
inserted_browse = False
for i, line in enumerate(lines):
    if not inserted_api and '"mode": "api"' in line and '"ssrf_blocked": True' in line:
        # Find the closing `)` of this return block
        j = i + 1
        while j < len(lines) and lines[j].strip() == ")":
            j += 1
        # j is now at empty line or next code; insert after empty line
        if j < len(lines) and lines[j].strip() == "":
            j += 1
        lines.insert(j, reval_block)
        inserted_api = True
        print(f"Inserted reval block in _execute_api_step after line {j+1}")
        break

# Re-read since we inserted
with open(path) as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if not inserted_browse and i > 350 and '"mode": "browse"' in line and '"ssrf_blocked": True' in line:
        j = i + 1
        while j < len(lines) and lines[j].strip() == ")":
            j += 1
        if j < len(lines) and lines[j].strip() == "":
            j += 1
        # Use browse-specific metadata for this block
        browse_reval = reval_block.replace('"mode": "api"', '"mode": "browse"')
        browse_reval = browse_reval.replace("(pinned IP): {url}", "(pinned IP browse): {url}")
        lines.insert(j, browse_reval)
        inserted_browse = True
        print(f"Inserted reval block in _execute_browse_step after line {j+1}")
        break

with open(path, "w") as f:
    f.writelines(lines)
print(f"Done - api={inserted_api}, browse={inserted_browse}")
