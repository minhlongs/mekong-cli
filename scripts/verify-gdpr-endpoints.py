#!/usr/bin/env python3
"""
GDPR Endpoints Verification Script
Tests all GDPR user rights endpoints for functionality.
Run: python3 scripts/verify-gdpr-endpoints.py --api-url http://localhost:8000 --token $ADMIN_TOKEN
"""
import argparse
import sys
from typing import Tuple

import requests


def test_endpoint(method: str, url: str, token: str, data=None) -> Tuple[bool, dict]:
    """Test a single endpoint and return success status and response."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, json=data or {}, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return False, {"error": f"Unknown method {method}"}
        
        return 200 <= resp.status_code < 300, {"status": resp.status_code, "body": resp.json() if resp.content else {}}
    except Exception as e:
        return False, {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Verify GDPR endpoints")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API gateway URL")
    parser.add_argument("--token", required=True, help="Admin token for authentication")
    parser.add_argument("--test-user", default="opc_test_abc123", help="User ID for testing")
    args = parser.parse_args()

    base = args.api_url.rstrip("/")
    token = args.token
    user_id = args.test_user

    print("=" * 60)
    print("GDPR ENDPOINTS VERIFICATION")
    print("=" * 60)

    tests = [
        ("GET", f"{base}/v1/user/{user_id}/data-export", "Data Export (Art. 15/20)"),
        ("GET", f"{base}/v1/user/{user_id}/consent/history", "Consent History (Art. 12)"),
        ("PUT", f"{base}/v1/user/{user_id}/profile", "Profile Update (Art. 16)"),
        ("DELETE", f"{base}/v1/user/{user_id}/account", "Account Deletion (Art. 17)"),
        ("POST", f"{base}/v1/user/{user_id}/consent/withdraw", "Consent Withdrawal (Art. 7)"),
    ]

    results = []
    for method, url, name in tests:
        print(f"\nTesting: {name}")
        print(f"  Endpoint: {method} {url.split('/v1/')[1]}")
        
        data = None
        if method == "PUT" and "profile" in url:
            data = {"user_id": user_id, "city": "Test City"}
        elif method == "DELETE":
            data = {"user_id": user_id, "confirmation": True}
        elif method == "POST" and "withdraw" in url:
            data = {"user_id": user_id, "consent_types": ["marketing"], "confirmation": True}
        
        success, response = test_endpoint(method, url, token, data)
        results.append((name, success, response))
        
        if success:
            print(f"  ✅ Status: {response.get('status', 'N/A')}")
        else:
            print(f"  ❌ Status: {response.get('status', 'ERROR')}")
            if "error" in response:
                print(f"     Error: {response['error']}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, _ in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} endpoints responding")
    
    if passed == total:
        print("\n✅ All GDPR endpoints are functional!")
        return 0
    else:
        print(f"\n❌ {total - passed} endpoint(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
