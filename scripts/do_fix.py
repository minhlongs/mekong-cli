
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Strategy: replace entire _validate_url function (lines 119-159)
# by finding its boundaries and substituting

# Find start: @staticmethod line
start = None
for i, line in enumerate(lines):
    if "@staticmethod" in line and i < 130:
        start = i
        break

# Find end: next def at class level
end = None
for i in range(start + 1, len(lines)):
    if lines[i].startswith("def ") and not lines[i].startswith("    "):
        end = i
        break

print(f"Replacing lines {start+1}-{end}")

new_lines = [
    'def _validate_url(self, url: str) -> tuple:\n',
    '    """Validate URL against SSRF attacks with IP pinning.\n',
    '\n',
    '    Resolves hostname to IP, checks against blocked networks, and returns\n',
    '    the resolved IP for callers to re-validate immediately before the\n',
    '    HTTP request (prevents DNS rebinding / TOCTOU attacks).\n',
    '\n',
    '    Args:\n',
    '        url: The URL to validate.\n',
    '\n',
    '    Returns:\n',
    '        (error_message, pinned_ip) -- error_message is None if safe,\n',
    '        pinned_ip is the resolved IP string (or None if unresolvable).\n',
    '    """\n',
    '    try:\n',
    '        parsed = urlparse(url)\n',
    '        host = parsed.hostname or ""\n',
    '        if not host:\n',
    '            return f"No hostname in URL: {url}", None\n',
    '\n',
    '        # Resolve IP and capture for pinning\n',
    '        try:\n',
    '            addr = ipaddress.ip_address(host)\n',
    '            pinned_ip = str(addr)\n',
    '        except ValueError:\n',
    '            # Resolve hostname - capture IP for pinning\n',
    '            try:\n',
    '                pinned_ip = socket.gethostbyname(host)\n',
    '                addr = ipaddress.ip_address(pinned_ip)\n',
    '            except (socket.gaierror, OSError, ValueError):\n',
    '                # Cannot resolve - allow (conservative: block only known-bad IPs)\n',
    '                return None, None\n',
    '\n',
    '        if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):\n',
    '            return None, None\n',
    '\n',
    '        # Check against all blocked networks\n',
    '        for network in _SSRF_BLOCKED_NETWORKS:\n',
    '            if addr in network:\n',
    '                return (\n',
    '                    f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",\n',
    '                    pinned_ip,\n',
    '                )\n',
    '\n',
    '        return None, pinned_ip\n',
    '    except Exception as e:\n',
    '        return f"URL validation error: {e}", None\n',
]

lines[start:end] = new_lines

# Now fix the two call sites
for i, line in enumerate(lines):
    if "ssrf_error = self._validate_url(url)" in line:
        lines[i] = line.replace("ssrf_error = self._validate_url(url)", "ssrf_error, pinned_ip = self._validate_url(url)")
        print(f"Fixed call at line {i+1}")

# Insert revalidation block after API SSRF check
for i, line in enumerate(lines):
    if "ssrf_error, pinned_ip" in line and "_execute_api_step" in "".join(lines[max(0,i-20):i]):
        # Find the closing ) of the early return block
        for j in range(i+1, min(i+15, len(lines))):
            if lines[j].strip() == ")":
                # Insert after this line
                reval = [
                    "\n",
                    "        # Re-validate pinned IP immediately before request (defense-in-depth\n",
                    '        # against DNS rebinding: if DNS changed since validation, block it).\n',
                    "        if pinned_ip:\n",
                    "            _addr = ipaddress.ip_address(pinned_ip)\n",
                    "            for network in _SSRF_BLOCKED_NETWORKS:\n",
                    "                if _addr in network:\n",
                    '                    self.console.print(\n',
                    '                        f"[bold red]SECURITY:[/bold red] "\n',
                    '                        f"SSRF blocked - pinned IP {pinned_ip} in blocked range {network}"\n',
                    "                    )\n",
                    "                    return ExecutionResult(\n",
                    "                        exit_code=1,\n",
                    '                        stdout="",\n',
                    '                        stderr=f"SSRF blocked (pinned IP): {url}",\n',
                    '                        metadata={"mode": "api", "ssrf_blocked": True},\n',
                    "                    )\n",
                ]
                for k, rl in enumerate(reval):
                    lines.insert(j + 1 + k, rl)
                print(f"Inserted API reval block at line {j+2}")
                break
        break

# Insert revalidation block after browse SSRF check
for i, line in enumerate(lines):
    if "ssrf_error, pinned_ip" in line and "_execute_browse_step" in "".join(lines[max(0,i-20):i]):
        for j in range(i+1, min(i+15, len(lines))):
            if lines[j].strip() == ")":
                reval = [
                    "\n",
                    "        # Re-validate pinned IP immediately before browser fetch (DNS rebinding guard)\n",
                    "        if pinned_ip:\n",
                    "            _addr = ipaddress.ip_address(pinned_ip)\n",
                    "            for network in _SSRF_BLOCKED_NETWORKS:\n",
                    "                if _addr in network:\n",
                    '                    self.console.print(\n',
                    '                        f"[bold red]SECURITY:[/bold red] "\n',
                    '                        f"SSRF blocked - pinned IP {pinned_ip} in blocked range {network}"\n',
                    "                    )\n",
                    "                    return ExecutionResult(\n",
                    "                        exit_code=1,\n",
                    '                        stdout="",\n',
                    '                        stderr=f"SSRF blocked (pinned IP browse): {url}",\n',
                    '                        metadata={"mode": "browse", "ssrf_blocked": True},\n',
                    "                    )\n",
                ]
                for k, rl in enumerate(reval):
                    lines.insert(j + 1 + k, rl)
                print(f"Inserted Browse reval block at line {j+2}")
                break
        break

with open(path, "w") as f:
    f.writelines(lines)
print("Done")
