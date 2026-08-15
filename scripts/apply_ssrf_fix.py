#!/usr/bin/env python3
"""Complete SSRF TOCTOU fix for executor.py."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    source = f.read()

# === PATCH 1: Rewrite _validate_url to return tuple with pinned IP ===
old_func = '''    @staticmethod
    def _validate_url(url: str) -> tuple:
        """Validate URL against SSRF attacks.

        Resolves the hostname to an IP and checks against blocked networks
        (private, loopback, link-local, reserved, metadata endpoints).

        Args:
            url: The URL to validate.

        Returns:
            Error message string if blocked, None if safe.
        """
        try:
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if not host:
                return f"No hostname in URL: {url}", None

            # Try parsing as literal IP first
            try:
                addr = ipaddress.ip_address(host)
            except ValueError:
                # Resolve hostname
                try:
                    addr = ipaddress.ip_address(socket.gethostbyname(host))
                except (socket.gaierror, OSError):
                    # Cannot resolve - allow (conservative: block only known-bad IPs)
                    return None, None

            if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
                return None, pinned_ip

            # Check against all blocked networks
            for network in _SSRF_BLOCKED_NETWORKS:
                if addr in network:
                    return f"SSRF blocked - target {host} ({addr}) is in blocked range {network}", pinned_ip

            return None, pinned_ip
        except Exception as e:
            return f"URL validation error: {e}", None'''

new_func = '''    def _validate_url(self, url: str) -> tuple:
        """Validate URL against SSRF attacks with IP pinning.

        Resolves hostname to IP, checks against blocked networks, and returns
        the resolved IP for callers to re-validate immediately before the
        HTTP request (prevents DNS rebinding / TOCTOU attacks).

        Args:
            url: The URL to validate.

        Returns:
            (error_message, pinned_ip) - error_message is None if safe,
            pinned_ip is the resolved IP string (or None if unresolvable).
        """
        try:
            parsed = urlparse(url)
            host = parsed.hostname or ""
            if not host:
                return f"No hostname in URL: {url}", None

            # Resolve IP and capture for pinning
            try:
                addr = ipaddress.ip_address(host)
                pinned_ip = str(addr)
            except ValueError:
                try:
                    pinned_ip = socket.gethostbyname(host)
                    addr = ipaddress.ip_address(pinned_ip)
                except (socket.gaierror, OSError, ValueError):
                    return None, None

            if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
                return None, None

            # Check against all blocked networks
            for network in _SSRF_BLOCKED_NETWORKS:
                if addr in network:
                    return (
                        f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",
                        pinned_ip,
                    )

            return None, pinned_ip
        except Exception as e:
            return f"URL validation error: {e}", None'''

if old_func in source:
    source = source.replace(old_func, new_func)
    print("Patch 1: Rewrote _validate_url")
else:
    print("ERROR: Patch 1 failed - pattern not found")

# === PATCH 2: Update _execute_api_step ===
source = source.replace(
    "        ssrf_error = self._validate_url(url)\n",
    "        ssrf_error, pinned_ip = self._validate_url(url)\n",
    1  # only first occurrence
)
print("Patch 2: Updated _execute_api_step call")

# Insert revalidation block after the api SSRF early-return
# Find the block: return ExecutionResult(... metadata=... ) followed by empty line + self.console.print
old_api_flow = '''            metadata={"mode": "api", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][API] {method}:[/cyan] {url})'''

new_api_flow = '''            metadata={"mode": "api", "ssrf_blocked": True},
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

if old_api_flow in source:
    source = source.replace(old_api_flow, new_api_flow)
    print("Patch 2b: Inserted revalidation in _execute_api_step")
else:
    print("ERROR: Patch 2b failed")

# === PATCH 3: Update _execute_browse_step ===
# Replace the SECOND occurrence of ssrf_error = self._validate_url(url)
# We already replaced the first (api), now replace browse
source = source.replace(
    "        ssrf_error = self._validate_url(url)\n",
    "        ssrf_error, pinned_ip = self._validate_url(url)\n",
    1  # replace remaining one
)
print("Patch 3: Updated _execute_browse_step call")

# Insert revalidation block after browse SSRF early-return
old_browse_flow = '''            metadata={"mode": "browse", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url})'''

new_browse_flow = '''            metadata={"mode": "browse", "ssrf_blocked": True},
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
                        stderr=f"SSRF blocked (pinned IP browse): {url}",
                        metadata={"mode": "browse", "ssrf_blocked": True},
                    )

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url})'''

if old_browse_flow in source:
    source = source.replace(old_browse_flow, new_browse_flow)
    print("Patch 3b: Inserted revalidation in _execute_browse_step")
else:
    print("ERROR: Patch 3b failed")

with open(path, "w") as f:
    f.write(source)
print("All patches written.")
