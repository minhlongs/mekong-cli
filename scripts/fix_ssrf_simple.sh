#!/bin/bash
# Fix SSRF TOCTOU in executor.py
FILE="/Users/macbook/mekong-cli/src/core/executor.py"

# Step 1: Change return type
sed -i '' 's/def _validate_url(url: str) --> str | None:/def _validate_url(self, url: str) -> tuple:/' "$FILE"

# Step 2: Remove @staticmethod
sed -i '' '/^    @staticmethod$/d' "$FILE"

# Step 3: Update no-hostname return
sed -i '' 's/return f"No hostname in URL: {url}"/return f"No hostname in URL: {url}", None/' "$FILE"

# Step 4: Add pinned_ip capture after literal IP parse
sed -i '' '/addr = ipaddress.ip_address(host)$/a\\        pinned_ip = str(addr)' "$FILE"

# Step 5: Split gethostbyname line into two
sed -i '' 's/addr = ipaddress.ip_address(socket.gethostbyname(host))/pinned_ip = socket.gethostbyname(host)\n                addr = ipaddress.ip_address(pinned_ip)/' "$FILE"

# Step 6: Add ValueError to exception handler
sed -i '' 's/except (socket.gaierror, OSError):/except (socket.gaierror, OSError, ValueError):/' "$FILE"

# Step 7: Update unresolved return
sed -i '' 's/# Cannot resolve.*$/Cannot resolve - allow (conservative: block only known-bad IPs)/' "$FILE"
# Find the "return None" after "Cannot resolve" and change it
python3 -c "
import re
with open('$FILE') as f:
    content = f.read()
# Fix: return None after Cannot resolve -> return None, None
content = content.replace(
    '# Cannot resolve - allow (conservative: block only known-bad IPs)\n                return None, None',
    '# Cannot resolve - allow (conservative: block only known-bad IPs)\n                return None, None'
)
# Fix isinstance fallback
content = content.replace(
    'if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):\n            return None, pinned_ip',
    'if not isinstance(addr, (ipaddress.IPv4Address, ipaddress.IPv6Address)):\n            return None, None'
)
# Fix blocked network return - convert to tuple
content = content.replace(
    'return f\"SSRF blocked - target {host} ({addr}) is in blocked range {network}\"',
    'return (\n                    f\"SSRF blocked - target {host} ({addr}) is in blocked range {network}\",\n                    pinned_ip,\n                )'
)
# Fix final success return
content = content.replace(
    'return None, pinned_ip\n    except Exception',
    'return None, pinned_ip\n    except Exception'
)
# Fix exception handler return
content = content.replace(
    'return f\"URL validation error: {e}\"',
    'return f\"URL validation error: {e}\", None'
)
with open('$FILE', 'w') as f:
    f.write(content)
print('Done')
"
echo "All fixes applied"
