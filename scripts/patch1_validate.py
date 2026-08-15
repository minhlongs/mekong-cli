
path = "/Users/macbook/mekong-cli/src/core/executor.py"
with open(path) as f:
    lines = f.readlines()

# Work on a copy
lines = list(lines)

# 1) Remove @staticmethod before _validate_url
for i in range(len(lines)):
    if "@staticmethod" in lines[i] and i < 130:
        lines[i] = ""
        break

# 2) Change _validate_url to instance method + tuple return
for i in range(len(lines)):
    if "def _validate_url(url: str) -> str | None:" in lines[i]:
        lines[i] = lines[i].replace("def _validate_url(url: str)", "def _validate_url(self, url: str)")
        lines[i] = lines[i].replace("-> str | None:", "-> tuple:")
        break

# 3) Add ", None" to no-hostname return
for i in range(len(lines)):
    if 'return f"No hostname in URL: {url}"' in lines[i] and ", None" not in lines[i]:
        lines[i] = lines[i].rstrip() + ", None\n"
        break

# 4) Add pinned_ip = str(addr) after literal IP parse
for i in range(len(lines)):
    if "addr = ipaddress.ip_address(host)" in lines[i] and "pinned_ip" not in lines[i]:
        indent = "        "
        lines[i] = indent + "addr = ipaddress.ip_address(host)\n"
        lines.insert(i+1, indent + "pinned_ip = str(addr)\n")
        break

# 5) Split gethostbyname line
for i in range(len(lines)):
    if "ipaddress.ip_address(socket.gethostbyname(host))" in lines[i]:
        indent = "                "
        lines[i] = indent + "pinned_ip = socket.gethostbyname(host)\n"
        lines.insert(i+1, indent + "addr = ipaddress.ip_address(pinned_ip)\n")
        break

# 6) Add ValueError to exception handler
for i in range(len(lines)):
    if "except (socket.gaierror, OSError):" in lines[i]:
        lines[i] = lines[i].replace("OSError):", "OSError, ValueError):")
        break

# 7) Fix unresolved return (after Cannot resolve comment)
for i in range(len(lines)):
    if "Cannot resolve" in lines[i] and i+1 < len(lines):
        if "return None" in lines[i+1] and ", None" not in lines[i+1]:
            lines[i+1] = lines[i+1].replace("return None", "return None, None")
            break

# 8) Fix isinstance fallback
for i in range(len(lines)):
    if "not isinstance(addr" in lines[i] and i+1 < len(lines):
        if lines[i+1].strip() == "return None":
            lines[i+1] = lines[i+1].replace("return None", "return None, None")
            break

# 9) Fix blocked network return - convert to tuple
for i in range(len(lines)):
    if "SSRF blocked - target {host} ({addr}) is in blocked range {network}" in lines[i]:
        indent = "                "
        lines[i] = indent + "return (\n"
        lines.insert(i+1, indent + "    f\"SSRF blocked - target {host} ({addr}) is in blocked range {network}\",\n")
        lines.insert(i+2, indent + "    pinned_ip,\n")
        lines.insert(i+3, indent + ")\n")
        break

# 10) Fix final success return in _validate_url
for i in range(len(lines)):
    if i > 140 and i < 170 and lines[i].strip() == "return None":
        if "for network" in lines[i-1] or "_SSRF_BLOCKED_NETWORKS" in lines[i-2]:
            lines[i] = lines[i].replace("return None", "return None, pinned_ip")
            break

# 11) Fix exception handler return
for i in range(len(lines)):
    if i > 140 and i < 170 and "except Exception as e:" in lines[i]:
        if i+1 < len(lines) and "return f" in lines[i+1] and ", None" not in lines[i+1]:
            lines[i+1] = lines[i+1].rstrip() + ", None\n"
            break

with open(path, "w") as f:
    f.writelines(lines)
print("Patch 1 complete: _validate_url fixed")
