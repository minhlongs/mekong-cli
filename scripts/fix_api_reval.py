#!/usr/bin/env python3
"""Final fix: insert re-validation block in _execute_api_step only."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    source = f.read()

# The API step revalidation was never inserted.
# Find the SSRF block in _execute_api_step and insert reval after it.
# Unique marker: the block between ssrf_error check and "[cyan][API]" print

marker = '''            metadata={"mode": "api", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][API] {method}:[/cyan] {url})'''

replacement = '''            metadata={"mode": "api", "ssrf_blocked": True},
            )

        # Re-validate pinned IP immediately before request (defense-in-depth
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

        self.console.print(f"[cyan][API] {method}:[/cyan] {url})'''

if marker in source:
    source = source.replace(marker, replacement, 1)
    print("Inserted reval block in _execute_api_step")
else:
    print("ERROR: marker not found")

with open(path, "w") as f:
    f.write(source)
print("Done")
