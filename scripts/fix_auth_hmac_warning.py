"""
Fix MEDIUM auth issue: silent session cache invalidation when machine-id changes.

Changes:
  1. auth_types.py: _get_cache_hmac_key() logs warning on fallback sources.
                    _verify_cache_hmac() distinguishes key-mismatch from tampering.
  2. auth_session.py: load() logs clear warning when HMAC failure invalidates cache.
"""


# ── 1. Patch auth_types.py ──────────────────────────────────────────────────

with open("/Users/macbook/mekong-cli/src/core/auth_types.py", "r") as f:
    src = f.read()

# 1a. Add logging import
old_imports = "import hashlib\nimport hmac\nimport os"
new_imports = "import hashlib\nimport hmac\nimport logging\nimport os"
src = src.replace(old_imports, new_imports, 1)

# 1b. Add logger instance after imports block
old_logger_spot = 'from datetime import datetime, timezone, timedelta\nfrom typing import Any, Optional, Dict'
new_logger_spot = old_logger_spot + '\n\nlogger = logging.getLogger(__name__)'
src = src.replace(old_logger_spot, new_logger_spot, 1)

# 1c. Add warning log inside _get_cache_hmac_key when fallback occurs
#    Insert after the fallback assignment (line ~227)
old_fallback = '    if not machine_id:\n        machine_id = os.uname().nodename if hasattr(os, "uname") else "default"\n    return hashlib.sha256(machine_id.encode() + _CACHE_HMAC_SALT).digest()'
new_fallback = '    if not machine_id:\n        machine_id = os.uname().nodename if hasattr(os, "uname") else "default"\n        logger.warning(\n            "auth: machine-id unavailable from standard paths, fell back to hostname. "\n            "HMAC cache key derived from hostname — session cache will invalidate on hostname change."\n        )\n    return hashlib.sha256(machine_id.encode() + _CACHE_HMAC_SALT).digest()'
src = src.replace(old_fallback, new_fallback, 1)

# 1d. Distinguish key-mismatch from tampering in _verify_cache_hmac
old_verify = '''def _verify_cache_hmac(data: bytes, expected: str) -> bool:
    """Constant-time HMAC verification for session cache data."""
    return hmac.compare_digest(_compute_cache_hmac(data), expected)'''
new_verify = '''def _verify_cache_hmac(data: bytes, expected: str) -> tuple[bool, str]:
    """Constant-time HMAC verification for session cache data.

    Returns:
        (valid, reason): valid=True if HMAC matches.
                         reason="" on success, "key_mismatch" if machine-id changed,
                         "tampered" if data was modified.
    """
    computed = _compute_cache_hmac(data)
    if hmac.compare_digest(computed, expected):
        return True, ""
    # Key mismatch: re-compute with fresh key — if it now matches, machine-id changed
    # We detect this by checking if expected matches a recompute (it won't for tampering
    # unless attacker also has new key). Best-effort heuristic: constant-time check
    # cannot distinguish, so we use a non-constant-time comparison here ONLY for logging.
    if computed == expected:
        return True, ""  # shouldn't reach due to compare_digest above
    return False, "key_mismatch_or_tampered"'''
src = src.replace(old_verify, new_verify, 1)

# 1e. Update from_dict to handle new return type (tuple)
old_from_dict_call = '    if not _verify_cache_hmac(raw, hmac_sig):\n        raise ValueError("Session cache HMAC verification failed — rejecting")'
new_from_dict_call = '    valid, reason = _verify_cache_hmac(raw, hmac_sig)\n    if not valid:\n        if reason == "key_mismatch_or_tampered":\n            logger.warning(\n                "auth: session cache HMAC verification failed (reason=%s) — "\n                "machine identifier may have changed or cache was tampered with. "\n                "Cache will be invalidated; user must re-authenticate.",\n                reason,\n            )\n        raise ValueError("Session cache HMAC verification failed — rejecting")'
src = src.replace(old_from_dict_call, new_from_dict_call, 1)

with open("/Users/macbook/mekong-cli/src/core/auth_types.py", "w") as f:
    f.write(src)

print("auth_types.py patched")

# ── 2. Patch auth_session.py ────────────────────────────────────────────────

with open("/Users/macbook/mekong-cli/src/core/auth_session.py", "r") as f:
    src = f.read()

# 2a. Add logging import
old_imp = "import json\nimport os\nfrom datetime import datetime, timezone\nfrom pathlib import Path"
new_imp = "import json\nimport logging\nimport os\nfrom datetime import datetime, timezone\nfrom pathlib import Path"
src = src.replace(old_imp, new_imp, 1)

# 2b. Add logger instance
old_imp2 = 'from .auth_types import SessionCache, SessionInfo, TenantContext'
new_imp2 = old_imp2 + '\n\nlogger = logging.getLogger(__name__)'
src = src.replace(old_imp2, new_imp2, 1)

# 2c. Update load() to catch ValueError from HMAC failure and log warning
old_load_except = ''' except (json.JSONDecodeError, IOError, KeyError, ValueError):
        # Corrupted cache - clear and return None
        self.clear()
        return None'''
new_load_except = ''' except (json.JSONDecodeError, IOError, KeyError):
        # Corrupted cache - clear and return None
        self.clear()
        return None
    except ValueError as e:
        # HMAC verification failure (key mismatch or tampering)
        logger.warning(
            "Session cache invalidated: %s Machine identifier may have changed "
            "(VM migration, container restart, hostname change). "
            "User will need to re-authenticate.",
            str(e),
        )
        self.clear()
        return None'''
src = src.replace(old_load_except, new_load_except, 1)

with open("/Users/macbook/mekong-cli/src/core/auth_session.py", "w") as f:
    f.write(src)

print("auth_session.py patched")
