"""Apply 3 fixes to stripe_integration.py - read file to confirm state first."""

with open('src/auth/stripe_integration.py', 'r', encoding='utf-8') as f:
    content = f.read()

errors = []

# Verify the file is clean (original state)
if 'SEC-011' not in content:
    errors.append("File doesn't contain SEC-011 comment - not the expected original")
if '_role_from_suffix' in content:
    errors.append("File already has _role_from_suffix - already patched")

if errors:
    for e in errors:
        print(f"ERROR: {e}")
    exit(1)

print("File confirmed as original, applying 3 fixes via content manipulation...")

# Fix 1: Insert _SUFFIX_ROLE_MAP + _role_from_suffix after DEFAULT_TIER_TO_ROLE closing brace
# The file has 2 blank lines between } and def get_tier_to_role_mapping
old1 = '}\n\n\ndef get_tier_to_role_mapping() -> Dict[str, Role]:'
new1 = '''}
# Bounded allow-list: only known suffixes may trigger fallback matching.
_SUFFIX_ROLE_MAP: Dict[str, Role] = dict(DEFAULT_TIER_TO_ROLE)


def _role_from_suffix(price_id: str) -> Optional[Role]:
 """Return role if price_id ends with an allowed suffix; else None."""
 for suffix, role in _SUFFIX_ROLE_MAP.items():
  if price_id.endswith(suffix):
   return role
 return None


def get_tier_to_role_mapping() -> Dict[str, Role]:'''

if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Fix 1: Inserted _SUFFIX_ROLE_MAP + _role_from_suffix")
else:
    # Try with 3 blank lines
    old1b = '}\n\n\n\ndef get_tier_to_role_mapping() -> Dict[str, Role]:'
    if old1b in content:
        content = content.replace(old1b, new1, 1)
        print("Fix 1: Inserted _SUFFIX_ROLE_MAP + _role_from_suffix (3-blank variant)")
    else:
        errors.append("Fix 1: neither 2-blank nor 3-blank variant found")

# Fix 2: Defensive copy - only first occurrence in get_tier_to_role_mapping
old2 = 'return DEFAULT_TIER_TO_ROLE'
new2 = 'return dict(DEFAULT_TIER_TO_ROLE)'
idx = content.find(old2)
if idx != -1:
    content = content[:idx] + new2 + content[idx+len(old2):]
    print("Fix 2: defensive copy applied")
else:
    errors.append("Fix 2: not found")

# Fix 3: Monkey-patch approach - completely avoids modifying method body
# Insert before "# Convenience functions" at the bottom of the file
patch_code = '''# Apply suffix fallback to map_tier_to_role without modifying the method body.
# This layer automatically extends any tier_to_role mapping with bounded suffix lookup.
_orig_map = StripeService.map_tier_to_role

def _suffix_aware_map(self: StripeService, stripe_price_id: str) -> Optional[Role]:
 role = _orig_map(self, stripe_price_id)
 if role is not None:
  return role
 return _role_from_suffix(stripe_price_id)

StripeService.map_tier_to_role = _suffix_aware_map

'''

idx_conv = content.find('# Convenience functions')
if idx_conv != -1:
    line_start = content.rfind('\n', 0, idx_conv) + 1
    content = content[:line_start] + patch_code + content[line_start:]
    print("Fix 3: Monkey-patch applied to StripeService.map_tier_to_role")
else:
    errors.append("Fix 3: '# Convenience functions' not found")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(f"  - {e}")
else:
    with open('src/auth/stripe_integration.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("\nAll 3 fixes written successfully")
