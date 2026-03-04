#!/usr/bin/env python3
"""Hub Transformation Verification Script.

Tests BMAD integration and package structure.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all critical imports."""
    print("🔍 Testing package imports...")

    try:
        from packages.core.bmad.loader import BMADWorkflowLoader
        print("  ✅ bmad.loader")
    except ImportError as e:
        print(f"  ❌ bmad.loader: {e}")
        return False

    try:
        from packages.core.bmad.models import BMADWorkflow, WorkflowCatalog
        print("  ✅ bmad.models")
    except ImportError as e:
        print(f"  ❌ bmad.models: {e}")
        return False

    try:
        from packages.core.bmad.validator import WorkflowValidator
        print("  ✅ bmad.validator")
    except ImportError as e:
        print(f"  ❌ bmad.validator: {e}")
        return False

    try:
        from packages.core.bmad.catalog import WorkflowCatalog as PersistentCatalog
        print("  ✅ bmad.catalog")
    except ImportError as e:
        print(f"  ❌ bmad.catalog: {e}")
        return False

    return True


def test_bmad_loading():
    """Test BMAD workflow loading."""
    print("\n🔍 Testing BMAD workflow loading...")

    try:
        from packages.core.bmad.loader import BMADWorkflowLoader

        loader = BMADWorkflowLoader()
        print("  ✅ Loader initialized")
        print(f"  📊 Total workflows: {loader.catalog.total_count}")
        print(f"  🏷️  Agent types: {', '.join(loader.catalog.agent_types)}")

        if loader.catalog.total_count > 0:
            print("  ✅ Workflows loaded successfully")
            return True
        else:
            print("  ⚠️  Warning: No workflows found (check _bmad directory)")
            return True  # Not a critical failure

    except Exception as e:
        print(f"  ❌ Error loading workflows: {e}")
        return False


def test_symlink():
    """Test symlink structure."""
    print("\n🔍 Testing symlink structure...")

    workflows_path = project_root / "packages" / "core" / "bmad" / "workflows"

    if workflows_path.exists() and workflows_path.is_symlink():
        target = workflows_path.resolve()
        print(f"  ✅ Symlink exists: {workflows_path}")
        print(f"  🔗 Points to: {target}")

        if target.exists():
            print("  ✅ Target exists")
            return True
        else:
            print("  ❌ Target does not exist")
            return False
    else:
        print(f"  ❌ Symlink not found at {workflows_path}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("HUB TRANSFORMATION VERIFICATION")
    print("=" * 60)
    print()

    tests = [
        ("Package Imports", test_imports),
        ("Symlink Structure", test_symlink),
        ("BMAD Loading", test_bmad_loading),
    ]

    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False

    print()
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED")
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
