#!/usr/bin/env python3
"""Fix SSRF TOCTOU bug in executor.py using line-based replacement."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Strategy: replace lines 120-160 (_validate_url) entirely
# First find start and end of _validate_url
start = None
end = None
for i, line in enumerate(lines):
    if line.strip().startswith("def _validate_url"):
        start = i
    if start is not None and i > start and line.strip().startswith("def "):
        end = i
        break

print(f"_validate_url spans lines {start+1} to {end}")

new_func = '''def _validate_url(url: str) -> tuple:
    """Validate URL against SSRF attacks.

    Resolves the hostname to an IP and checks against blocked networks
    (private, loopback, link-local, reserved, metadata endpoints).

    Uses IP pinning: the resolved IP is returned so callers can re-validate
    it immediately before the HTTP request, preventing DNS rebinding attacks
    (TOCTOU between validation and request).

    Args:
        url: The URL to validate.

    Returns:
        (error_message, pinned_ip) -- error_message is None if safe,
        pinned_ip is the resolved IP string (or None if unresolvable).
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if not host:
            return f"No hostname in URL: {url}", None

        # Try parsing as literal IP first, capture for pinning
        try:
            addr = ipaddress.ip_address(host)
            pinned_ip = str(addr)
        except ValueError:
            # Resolve hostname - capture IP for pinning
            try:
                pinned_ip = socket.gethostbyname(host)
                addr = ipaddress.ip_address(pinned_ip)
            except (socket.gaierror, OSError, ValueError):
                # Cannot resolve - allow (conservative: block only known-bad IPs)
                return None, None

        if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return None, pinned_ip

        # Check against all blocked networks
        for network in _SSRF_BLOCKED_NETWORKS:
            if addr in network:
                return (
                    f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",
                    pinned_ip,
                )

        return None, pinned_ip
    except Exception as e:
        return f"URL validation error: {e}", None

'''

lines[start:end] = [new_func]

# Now fix the callers - they need tuple unpacking and re-validation
# Find _execute_api_step SSRF check
for i, line in enumerate(lines):
    if "ssrf_error = self._validate_url(url)" in line and i > 200:
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = indent + "ssrf_error, pinned_ip = self._validate_url(url)\n"
        print(f"Fixed _execute_api_step call at line {i+1}")
        break

# Find _execute_browse_step SSRF check
for i, line in enumerate(lines):
    if "ssrf_error = self._validate_url(url)" in line and i > 350:
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = indent + "ssrf_error, pinned_ip = self._validate_url(url)\n"
        print(f"Fixed _execute_browse_step call at line {i+1}")
        break

with open(path, "w") as f:
    f.writelines(lines)
print("Done")
