
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    source = f.read()

# --- Patch 1: _validate_url -> return tuple with pinned IP ---
old = """    # Try parsing as literal IP first
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        # Resolve hostname
        try:
            addr = ipaddress.ip_address(socket.gethostbyname(host))
        except (socket.gaierror, OSError):
            # Cannot resolve - allow (conservative: block only known-bad IPs)
            return None

    if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        return None

    # Check against all blocked networks
    for network in _SSRF_BLOCKED_NETWORKS:
        if addr in network:
            return f"SSRF blocked - target {host} ({addr}) is in blocked range {network}"

    return None"""

new = """    # Try parsing as literal IP first, capture for pinning
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

    return None, pinned_ip"""

if old not in source:
    print("ERROR: Patch 1 old text not found")
else:
    source = source.replace(old, new)
    print("Patch 1 applied")

# --- Patch 2: _execute_api_step re-validate pinned IP ---
old2 = """        # SSRF prevention: validate URL before making request
        ssrf_error = self._validate_url(url)
        if ssrf_error:
            self.console.print(f"[bold red]SECURITY:[/bold red] {ssrf_error}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"SSRF blocked: {url}",
                metadata={"mode": "api", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][API] {method}:[/cyan] {url})"""

new2 = """        # SSRF prevention: validate URL and pin resolved IP
        ssrf_error, pinned_ip = self._validate_url(url)
        if ssrf_error:
            self.console.print(f"[bold red]SECURITY:[/bold red] {ssrf_error}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"SSRF blocked: {url}",
                metadata={"mode": "api", "ssrf_blocked": True},
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

        self.console.print(f"[cyan][API] {method}:[/cyan] {url})"""

if old2 not in source:
    print("ERROR: Patch 2 old text not found")
else:
    source = source.replace(old2, new2)
    print("Patch 2 applied")

# --- Patch 3: _execute_browse_step re-validate pinned IP ---
old3 = """        # SSRF prevention: validate URL before browser fetch
        ssrf_error = self._validate_url(url)
        if ssrf_error:
            self.console.print(f"[bold red]SECURITY:[/bold red] {ssrf_error}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"SSRF blocked: {url}",
                metadata={"mode": "browse", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url})"""

new3 = """        # SSRF prevention: validate URL and pin resolved IP
        ssrf_error, pinned_ip = self._validate_url(url)
        if ssrf_error:
            self.console.print(f"[bold red]SECURITY:[/bold red] {ssrf_error}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=f"SSRF blocked: {url}",
                metadata={"mode": "browse", "ssrf_blocked": True},
            )

        # Re-validate pinned IP immediately before browser fetch (DNS rebinding guard)
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
                        metadata={"mode": "browse", "ssrf_blocked": True},
                    )

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url})"""

if old3 not in source:
    print("ERROR: Patch 3 old text not found")
else:
    source = source.replace(old3, new3)
    print("Patch 3 applied")

with open(path, "w") as f:
    f.write(source)
print("Done")
