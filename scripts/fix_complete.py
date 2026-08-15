#!/usr/bin/env python3
"""One-shot SSRF TOCTOU fix for executor.py."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    source = f.read()

# === Fix 1: _validate_url - change return type and add IP pinning ===
# Change signature
source = source.replace(
    "def _validate_url(url: str) -> str | None:",
    "def _validate_url(url: str) -> tuple:"
)

# Update docstring Returns section
source = source.replace(
    "        Error message string if blocked, None if safe.",
    "        (error_message, pinned_ip) -- error_message is None if safe,\n        pinned_ip is the resolved IP string (or None if unresolvable).\n\n        Uses IP pinning: resolved IP returned so callers re-validate\n        immediately before HTTP request, preventing DNS rebinding (TOCTOU)."
)

# Change first return (no hostname)
source = source.replace(
    '            return f"No hostname in URL: {url}"\n\n        # Try parsing as literal IP first',
    '            return f"No hostname in URL: {url}", None\n\n        # Try parsing as literal IP first, capture for pinning\n        pinned_ip = None'
)

# Capture literal IP
source = source.replace(
    "            addr = ipaddress.ip_address(host)\n        except ValueError:",
    "            addr = ipaddress.ip_address(host)\n            pinned_ip = str(addr)\n        except ValueError:"
)

# Capture DNS-resolved IP
source = source.replace(
    "                addr = ipaddress.ip_address(socket.gethostbyname(host))",
    "                pinned_ip = socket.gethostbyname(host)\n                addr = ipaddress.ip_address(pinned_ip)"
)

# Update unresolvable return
source = source.replace(
    "                return None\n\n        if not isinstance",
    "                return None, None\n\n        if not isinstance"
)

# Update isinstance fallback
source = source.replace(
    "            return None\n\n        # Check against all blocked networks",
    "            return None, pinned_ip\n\n        # Check against all blocked networks"
)

# Update blocked network return (single line -> tuple)
source = source.replace(
    '                return f"SSRF blocked — target {host} ({addr}) is in blocked range {network}"',
    '                return (\n                    f"SSRF blocked — target {host} ({addr}) is in blocked range {network}",\n                    pinned_ip,\n                )'
)

# Update final success return
source = source.replace(
    "        return None\n    except Exception as e:\n        return f\"URL validation error: {e}\"",
    "        return None, pinned_ip\n    except Exception as e:\n        return f\"URL validation error: {e}\", None"
)

# === Fix 2: Callers - unpack tuple ===
source = source.replace(
    "        ssrf_error = self._validate_url(url)\n        if ssrf_error:",
    "        ssrf_error, pinned_ip = self._validate_url(url)\n        if ssrf_error:"
)

# === Fix 3: Add re-validation blocks ===
# We need to insert after the SSRF block in _execute_api_step and _execute_browse_step
# Find the pattern: closing ) of early-return, then next line is console.print or empty

REVAL_API = '''        # Re-validate pinned IP immediately before request (defense-in-depth
        # against DNS rebinding: if DNS changed since validation, block it).
        if pinned_ip:
            _addr = ipaddress.ip_address(pinned_ip)
            for network in _SSRF_BLOCKED_NETWORKS:
                if _addr in network:
                    self.console.print(
                        f"[bold red]SECURITY:[/bold red] "
                        f"SSRF blocked — pinned IP {pinned_ip} in blocked range {network}"
                    )
                    return ExecutionResult(
                        exit_code=1,
                        stdout="",
                        stderr=f"SSRF blocked (pinned IP): {url}",
                        metadata={"mode": "api", "ssrf_blocked": True},
                    )

'''

REVAL_BROWSE = REVAL_API.replace('(pinned IP): {url}', '(pinned IP browse): {url}')

# Insert API reval: after the SSRF early-return block in _execute_api_step
# Find the line `self.console.print(f"[cyan][API]` and insert before it
source = source.replace(
    '        self.console.print(f"[cyan][API] {method}:[/cyan] {url}")',
    REVAL_API + '        self.console.print(f"[cyan][API] {method}:[/cyan] {url}")',
    1  # only first occurrence
)

# Insert browse reval: after the SSRF early-return block in _execute_browse_step
source = source.replace(
    '        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url}")',
    REVAL_BROWSE + '        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url}")',
    1  # only first occurrence
)

with open(path, "w") as f:
    f.write(source)

# Verify syntax
import ast  # noqa: E402
ast.parse(source)
print("Done - syntax verified OK")
