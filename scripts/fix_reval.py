#!/usr/bin/env python3
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Find the closing of the api SSRF block and insert revalidation after it
for i, line in enumerate(lines):
    if i > 280 and i < 300 and line.strip() == ")" and i > 0:
        # Check if previous lines are the SSRF return block
        prev = "".join(lines[max(0,i-8):i])
        if "ssrf_blocked" in prev and "mode" in prev:
            # Insert revalidation block
            reval = [
                "\n",
                "        # Re-validate pinned IP immediately before request\n",
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
                '                        stderr=f"SSRF blocked (pinned): {url}",\n',
                '                        metadata={"mode": "api", "ssrf_blocked": True},\n',
                "                    )\n",
            ]
            for j, l in enumerate(reval):
                lines.insert(i + 1 + j, l)
            print(f"Inserted api revalidation at line {i+2}")
            break

with open(path, "w") as f:
    f.writelines(lines)
print("Done")
