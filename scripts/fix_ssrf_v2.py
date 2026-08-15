#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    source = f.read()

# Patch 1: Change return type and add IP pinning to _validate_url
old_return_type = "def _validate_url(url: str) -> str | None:"
new_return_type = "def _validate_url(url: str) -> tuple:"
source = source.replace(old_return_type, new_return_type)

# Replace "return None" after socket error with "return None, None"
old_unresolvable = '''            except (socket.gaierror, OSError):
                # Cannot resolve - allow (conservative: block only known-bad IPs)
                return None'''
new_unresolvable = '''            except (socket.gaierror, OSError):
                # Cannot resolve - allow (conservative: block only known-bad IPs)
                return None, None'''
source = source.replace(old_unresolvable, new_unresolvable)

# Add pinned_ip capture for literal IP
old_literal_ip = '''        try:
            addr = ipaddress.ip_address(host)
        except ValueError:'''
new_literal_ip = '''        try:
            addr = ipaddress.ip_address(host)
            pinned_ip = str(addr)
        except ValueError:'''
source = source.replace(old_literal_ip, new_literal_ip)

# Capture IP from gethostbyname
old_dns_resolve = '''                addr = ipaddress.ip_address(socket.gethostbyname(host))'''
new_dns_resolve = '''                pinned_ip = socket.gethostbyname(host)
                addr = ipaddress.ip_address(pinned_ip)'''
source = source.replace(old_dns_resolve, new_dns_resolve)

# Update isinstance fallback return
old_isinstance = '''        if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return None'''
new_isinstance = '''        if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
            return None, pinned_ip'''
source = source.replace(old_isinstance, new_isinstance)

# Update blocked network return
old_blocked = '''                return f"SSRF blocked - target {host} ({addr}) is in blocked range {network}"'''
new_blocked = '''                return (
                    f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",
                    pinned_ip,
                )'''
source = source.replace(old_blocked, new_blocked)

# Update final success return
old_success = '''        return None'''
# Be careful: only change the one in _validate_url (after the for loop)
# Find the pattern "for network in _SSRF_BLOCKED_NETWORKS:" block and fix the return after it
source = source.replace(
    '''        for network in _SSRF_BLOCKED_NETWORKS:
            if addr in network:
                return (
                    f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",
                    pinned_ip,
                )

        return None''',
    '''        for network in _SSRF_BLOCKED_NETWORKS:
            if addr in network:
                return (
                    f"SSRF blocked - target {host} ({addr}) is in blocked range {network}",
                    pinned_ip,
                )

        return None, pinned_ip'''
)

# Patch 2: Update _execute_api_step
source = source.replace(
    "        ssrf_error = self._validate_url(url)",
    "        ssrf_error, pinned_ip = self._validate_url(url)"
)

# Add re-validation block after api check (before the console.print)
source = source.replace(
    '''            metadata={"mode": "api", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][API] {method}:[/cyan] {url})''',
    '''            metadata={"mode": "api", "ssrf_blocked": True},
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
)

# Patch 3: Update _execute_browse_step
source = source.replace(
    "        ssrf_error = self._validate_url(url)",
    "        ssrf_error, pinned_ip = self._validate_url(url)"
)

# Add re-validation block after browse check
source = source.replace(
    '''            metadata={"mode": "browse", "ssrf_blocked": True},
            )

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url})''',
    '''            metadata={"mode": "browse", "ssrf_blocked": True},
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

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url})'''
)

with open(path, "w") as f:
    f.write(source)
print("Done - all patches applied")
