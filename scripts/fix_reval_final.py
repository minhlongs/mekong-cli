#!/usr/bin/env python3
"""Fix revalidation blocks - ensure one in _execute_api_step and one in _execute_browse_step."""

path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Count how many revalidation blocks exist and where
reval_lines = []
for i, line in enumerate(lines):
    if "Re-validate pinned IP" in line:
        reval_lines.append(i)
print(f"Found revalidation blocks at lines: {[l+1 for l in reval_lines]}")

# Check what's between ssrf_error call and console.print for API (line ~288)
api_ssrf_line = None
browse_ssrf_line = None
for i, line in enumerate(lines):
    if "ssrf_error, pinned_ip = self._validate_url(url)" in line:
        if api_ssrf_line is None:
            api_ssrf_line = i
        else:
            browse_ssrf_line = i

print(f"API SSRF call at line {api_ssrf_line+1}")
print(f"Browse SSRF call at line {browse_ssrf_line+1}")

# Find next console.print after each SSRF call
for i in range(api_ssrf_line, len(lines)):
    if '[cyan][API]' in lines[i]:
        print(f"API console.print at line {i+1}: {lines[i].strip()}")
        break

for i in range(browse_ssrf_line, len(lines)):
    if '[cyan][Browse]' in lines[i]:
        print(f"Browse console.print at line {i+1}: {lines[i].strip()}")
        break

# Strategy: remove ALL revalidation blocks, then insert exactly one after each SSRF check
# Step 1: Remove existing revalidation blocks (in reverse order to preserve indices)
reval_blocks = []
current_block = []
for i, line in enumerate(lines):
    if "Re-validate pinned IP" in line:
        if current_block:
            reval_blocks.append(current_block)
        current_block = [(i, line)]
    elif current_block and ("SECURITY:" in line or "SSRF blocked" in line or "pinned_ip" in line or "_addr" in line or "for network" in line or "if _addr" in line or "return ExecutionResult" in line or "stderr=f" in line or "metadata=" in line):
        current_block.append((i, line))
        if ")" in line and "ExecutionResult" not in line and current_block:
            # End of block found
            reval_blocks.append(current_block)
            current_block = []
    elif current_block and line.strip() == "":
        reval_blocks.append(current_block)
        current_block = []

if current_block:
    reval_blocks.append(current_block)

print(f"Found {len(reval_blocks)} revalidation blocks")
for block in reval_blocks:
    start = block[0][0]
    end = block[-1][0]
    print(f"  Block at lines {start+1}-{end+1}")

# Remove blocks from end to start
for block in reversed(reval_blocks):
    start = block[0][0]
    end = block[-1][0] + 1
    # Find actual end (last non-empty line of block)
    actual_end = start
    for idx, (line_num, _) in enumerate(block):
        actual_end = line_num + 1
    del lines[start:actual_end]
    print(f"Removed block at lines {start+1}-{actual_end}")

# Now insert exactly one revalidation block after each SSRF check
reval_code = """        # Re-validate pinned IP immediately before request (defense-in-depth
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

api_reval = reval_code
browse_reval = reval_code.replace('(pinned IP): {url}', '(pinned IP browse): {url}')

# Find insertion points again
api_ssrf_line = None
browse_ssrf_line = None
for i, line in enumerate(lines):
    if "ssrf_error, pinned_ip = self._validate_url(url)" in line:
        if api_ssrf_line is None:
            api_ssrf_line = i
        else:
            browse_ssrf_line = i

# Insert after the SSRF block's closing `)` line
# Find the line with `)` that closes the early-return ExecutionResult
for i in range(api_ssrf_line, len(lines)):
    if lines[i].strip() == ")" and i > api_ssrf_line + 3:
        lines.insert(i + 1, api_reval)
        print(f"Inserted API reval block after line {i+1}")
        break

# Re-find browse line after insertion
for i, line in enumerate(lines):
    if "ssrf_error, pinned_ip = self._validate_url(url)" in line and i > api_ssrf_line + 1:
        browse_ssrf_line = i
        break

for i in range(browse_ssrf_line, len(lines)):
    if lines[i].strip() == ")" and i > browse_ssrf_line + 3:
        lines.insert(i + 1, browse_reval)
        print(f"Inserted Browse reval block after line {i+1}")
        break

with open(path, "w") as f:
    f.writelines(lines)
print("Done")
