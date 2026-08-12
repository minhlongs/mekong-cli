"""
Fix MEDIUM issue: Silent session cache wipe on HMAC key mismatch.

Changes:
- auth_types.py: Add logging + warnings for HMAC key fallback and verification failure
- auth_session.py: Add clear warning when load() invalidates cache due to HMAC failure
"""


# ── auth_types.py ──────────────────────────────────────────────────────────

path_auth_types = "/Users/macbook/mekong-cli/src/core/auth_types.py"

with open(path_auth_types, "r") as f:
    src = f.read()

# 1. Add `import logging` after the existing imports block
old_imports = """import hashlib
import hmac
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict"""

new_imports = """import hashlib
import hmac
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)"""

assert old_imports in src, "imports block not found"
src = src.replace(old_imports, new_imports)

# 2. Add warning log in _get_cache_hmac_key when falling back to nodename
old_fallback = '''    if not machine_id:
        machine_id = os.uname().nodename if hasattr(os, "uname") else "default"
    return hashlib.sha256(machine_id.encode() + _CACHE_HMAC_SALT).digest()'''

new_fallback = '''    if not machine_id:
        machine_id = os.uname().nodename if hasattr(os, "uname") else "default"
        logger.warning(
            "No machine-id found on /etc/machine-id or /var/lib/dbus/machine-id; "
            "falling back to hostname for HMAC key derivation. "
            "Key will change on host rename or container restart."
        )
    return hashlib.sha256(machine_id.encode() + _CACHE_HMAC_SALT).digest()'''

assert old_fallback in src, "fallback block not found"
src = src.replace(old_fallback, new_fallback)

# 3. Add warning log in _verify_cache_hmac on failure
old_verify = '''def _verify_cache_hmac(data: bytes, expected: str) -> bool:
    """Constant-time HMAC verification for session cache data."""
    return hmac.compare_digest(_compute_cache_hmac(data), expected)'''

new_verify = '''def _verify_cache_hmac(data: bytes, expected: str) -> bool:
    """Constant-time HMAC verification for session cache data.

    Returns False if key changed (migration/restart) or data tampered.
    Caller should inspect logs to distinguish the two causes.
    """
    computed = _compute_cache_hmac(data)
    valid = hmac.compare_digest(computed, expected)
    if not valid:
        logger.warning(
            "Session cache HMAC verification failed — "
            "possible causes: machine identifier changed (VM migration, "
            "container restart, host rename) or cache file tampered. "
            "Cache will be invalidated; user must re-authenticate."
        )
    return valid'''

assert old_verify in src, "verify block not found"
src = src.replace(old_verify, new_verify)

with open(path_auth_types, "w") as f:
    f.write(src)

print("auth_types.py patched OK")

# ── auth_session.py ────────────────────────────────────────────────────────

path_auth_session = "/Users/macbook/mekong-cli/src/core/auth_session.py"

with open(path_auth_session, "r") as f:
    src2 = f.read()

# 1. Add `import logging` after existing imports
old_imports2 = """import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .auth_types import SessionCache, SessionInfo, TenantContext"""

new_imports2 = """import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .auth_types import SessionCache, SessionInfo, TenantContext

logger = logging.getLogger(__name__)"""

assert old_imports2 in src2, "auth_session imports block not found"
src2 = src2.replace(old_imports2, new_imports2)

# 2. Split the broad except block so HMAC failures get a specific warning log
old_except = """    except (json.JSONDecodeError, IOError, KeyError, ValueError):
        # Corrupted cache - clear and return None
        self.clear()
        return None"""

new_except = """    except (json.JSONDecodeError, IOError, KeyError) as exc:
        # Corrupted or unreadable cache - clear and return None
        logger.debug("Session cache load failed (%s): %s", type(exc).__name__, exc)
        self.clear()
        return None
    except ValueError as exc:
        # HMAC verification failure (key mismatch or tampering)
        logger.warning(
            "Session cache invalidated: %s "
            "User will need to re-authenticate.",
            exc,
        )
        self.clear()
        return None"""

assert old_except in src2, "except block not found"
src2 = src2.replace(old_except, new_except)

with open(path_auth_session, "w") as f:
    f.write(src2)

print("auth_session.py patched OK")

# ── Syntax check ────────────────────────────────────────────────────────────

import py_compile  # noqa: E402
import sys  # noqa: E402

for p in (path_auth_types, path_auth_session):
    try:
        py_compile.compile(p, doraise=True)
        print(f"  syntax OK: {p}")
    except py_compile.PyCompileError as e:
        print(f"  SYNTAX ERROR in {p}: {e}", file=sys.stderr)
        sys.exit(1)

print("\nAll done. Summary below.")
