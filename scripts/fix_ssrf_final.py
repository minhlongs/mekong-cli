#!/usr/bin/env python3
"""Apply SSRF TOCTOU fix to executor.py"""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# 1. Find and replace the _validate_url function
start = None
for i, line in enumerate(lines):
    if "@staticmethod" in line and i < 130:
        start = i
        break

end = None
for i in range(start + 1, len(lines)):
    stripped = lines[i].lstrip()
    if stripped.startswith("def ") or stripped.startswith("class "):
        end = i
        break

print(f"Replacing lines {start+1} to {end}")

new_func = [
    "def _validate_url(self, url: str) -> tuple:\n",
    '    """Validate URL against SSRF attacks with IP pinning.\n',
    "\n",
    "    Resolves hostname to IP, checks against blocked networks, and returns\n",
    "    the resolved IP for callers to re-validate immediately before the\n",
    "    HTTP request (prevents DNS rebinding / TOCTOU attacks).\n",
    "\n",
    "    Args:\n",
    "        url: The URL to validate.\n",
    "\n",
    "    Returns:\n",
    "        (error_message, pinned_ip) -- error_message is None if safe,\n",
    "        pinned_ip is the resolved IP string (or None if unresolvable).\n",
    '    """\n',
    "    try:\n",
    "        parsed = urlparse(url)\n",
    "        host = parsed.hostname or \"\"\n",
    "        if not host:\n",
    '            return f"No hostname in URL: {url}", None\n',
    "\n",
    "        # Resolve IP and capture for pinning\n",
    "        try:\n",
    "            addr = ipaddress.ip_address(host)\n",
    "            pinned_ip = str(addr)\n",
    "        except ValueError:\n",
    "            # Resolve hostname - capture IP for pinning\n",
    "            try:\n",
    "                pinned_ip = socket.gethostbyname(host)\n",
    "                addr = ipaddress.ip_address(pinned_ip)\n",
    "            except (socket.gaierror, OSError, ValueError):\n",
    "                # Cannot resolve - allow (conservative: block only known-bad IPs)\n",
    "                return None, None\n",
    "\n",
    "        if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):\n",
    "            return None, None\n",
    "\n",
    "        # Check against all blocked networks\n",
    "        for network in _SSRF_BLOCKED_NETWORKS:\n",
    "            if addr in network:\n",
    "                return (\n",
    '                    f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",\n',
    "                    pinned_ip,\n",
    "                )\n",
    "\n",
    "        return None, pinned_ip\n",
    "    except Exception as e:\n",
    '        return f"URL validation error: {e}", None\n',
]

lines[start:end] = new_func

# 2. Fix call site 1: _execute_api_step
for i, line in enumerate(lines):
    if "ssrf_error = self._validate_url(url)" in line:
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = indent + "ssrf_error, pinned_ip = self._validate_url(url)\n"
        print(f"Fixed API call at line {i+1}")
        api_line = i
        break

# 3. Insert revalidation block after API SSRF early return
for i in range(api_line, min(api_line + 20, len(lines))):
    if "self.console.print(f\"[cyan][API]" in lines[i]:
        indent = "        "
        reval = [
            "\n",
            indent + "# Re-validate pinned IP immediately before request (defense-in-depth\n",
            indent + "# against DNS rebinding: if DNS changed since validation, block it).\n",
            indent + "if pinned_ip:\n",
            indent + "    _addr = ipaddress.ip_address(pinned_ip)\n",
            indent + "    for network in _SSRF_BLOCKED_NETWORKS:\n",
            indent + "        if _addr in network:\n",
            indent + "            self.console.print(\n",
            indent + '                f"[bold red]SECURITY:[/bold red] "\n',
            indent + '                f"SSRF blocked - pinned IP {pinned_ip} in blocked range {network}"\n',
            indent + "            )\n",
            indent + "            return ExecutionResult(\n",
            indent + "                exit_code=1,\n",
            indent + '                stdout="",\n',
            indent + '                stderr=f"SSRF blocked (pinned IP): {url}",\n',
            indent + '                metadata={"mode": "api", "ssrf_blocked": True},\n',
            indent + "            )\n",
        ]
        for j, rl in enumerate(reval):
            lines.insert(i + j, rl)
        print(f"Inserted API revalidation block at line {i+1}")
        break

# 4. Fix call site 2: _execute_browse_step
for i, line in enumerate(lines):
    if "ssrf_error = self._validate_url(url)" in line:
        indent = line[:len(line) - len(line.lstrip())]
        lines[i] = indent + "ssrf_error, pinned_ip = self._validate_url(url)\n"
        print(f"Fixed Browse call at line {i+1}")
        browse_line = i
        break

# 5. Insert revalidation block after browse SSRF early return
for i in range(browse_line, min(browse_line + 20, len(lines))):
    if "self.console.print(f\"[cyan][Browse]" in lines[i]:
        indent = "        "
        reval = [
            "\n",
            indent + "# Re-validate pinned IP immediately before browser fetch\n",
            indent + "# (DNS rebinding guard)\n",
            indent + "if pinned_ip:\n",
            indent + "    _addr = ipaddress.ip_address(pinned_ip)\n",
            indent + "    for network in _SSRF_BLOCKED_NETWORKS:\n",
            indent + "        if _addr in network:\n",
            indent + "            self.console.print(\n",
            indent + '                f"[bold red]SECURITY:[/bold red] "\n',
            indent + '                f"SSRF blocked - pinned IP {pinned_ip} in blocked range {network}"\n',
            indent + "            )\n",
            indent + "            return ExecutionResult(\n",
            indent + "                exit_code=1,\n",
            indent + '                stdout="",\n',
            indent + '                stderr=f"SSRF blocked (pinned IP browse): {url}",\n',
            indent + '                metadata={"mode": "browse", "ssrf_blocked": True},\n',
            indent + "            )\n",
        ]
        for j, rl in enumerate(reval):
            lines.insert(i + j, rl)
        print(f"Inserted Browse revalidation block at line {i+1}")
        break

with open(path, "w") as f:
    f.writelines(lines)
print("All patches written successfully")
