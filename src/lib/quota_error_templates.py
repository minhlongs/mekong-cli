# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Quota Error & Warning Context Models and Quota Templates — ROIaaS Phase 6b."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class QuotaErrorContext:
    """Context for formatting quota errors."""
    tier: str
    daily_used: int
    daily_limit: int
    command: str
    monthly_used: int = 0
    monthly_limit: int = 0
    retry_after_seconds: Optional[int] = None
    violation_type: str = "quota_exceeded"


@dataclass
class QuotaWarningContext:
    """Context for formatting quota warnings."""
    tier: str
    daily_used: int
    daily_limit: int
    percentage: float
    remaining: int
    command: str
    threshold: int = 80


WARNING_80_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🟡  Quota Warning: 80% Used                                 ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today ({percentage}%).║
║                                                              ║
║  Remaining: {remaining} commands                            ║
║                                                              ║
║  💡 Consider upgrading to Pro for 1000 commands/day:        ║
║     → https://raas.mekong.dev/pricing                        ║
╚══════════════════════════════════════════════════════════════╝
"""

WARNING_90_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🟠  Quota Warning: 90% Used                                 ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today ({percentage}%).║
║                                                              ║
║  ⚠️  Only {remaining} commands remaining!                   ║
║                                                              ║
║  🚀 Upgrade to Pro NOW to avoid interruption:               ║
║     → https://raas.mekong.dev/pricing                        ║
╚══════════════════════════════════════════════════════════════╝
"""

QUOTA_TEMPLATES = {
    "free": """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Free Tier Quota Exceeded                                ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today.     ║
║                                                              ║
║  Command '{command}' requires additional quota.              ║
║                                                              ║
║  💡 Upgrade to Pro for 1000 commands/day:                   ║
║     → https://raas.mekong.dev/pricing                        ║
║                                                              ║
║  Plans:                                                      ║
║  • Trial: FREE (50 commands/day)                            ║
║  • Pro: $29/mo (1000 commands/day)                          ║
║  • Enterprise: Custom (Unlimited)                           ║
╚══════════════════════════════════════════════════════════════╝
""",
    "trial": """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Trial Quota Exceeded                                    ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today.     ║
║                                                              ║
║  Your trial quota is exhausted.                             ║
║                                                              ║
║  🚀 Upgrade to Pro to continue:                             ║
║     → https://raas.mekong.dev/pricing                        ║
║                                                              ║
║  Quota resets in: {retry_after}                             ║
╚══════════════════════════════════════════════════════════════╝
""",
    "starter": """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Starter Tier Quota Exceeded                             ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today.     ║
║                                                              ║
║  Quota resets in: {retry_after}                             ║
║                                                              ║
║  Need more? Upgrade to Pro:                                 ║
║     → https://raas.mekong.dev/pricing                        ║
╚══════════════════════════════════════════════════════════════╝
""",
    "growth": """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Growth Tier Quota Exceeded                              ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today.     ║
║                                                              ║
║  Quota resets in: {retry_after}                             ║
║                                                              ║
║  Need more? Upgrade to Enterprise:                          ║
║     → https://raas.mekong.dev/enterprise                     ║
╚══════════════════════════════════════════════════════════════╝
""",
    "pro": """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Daily Quota Exceeded                                    ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used}/{daily_limit} commands today.     ║
║                                                              ║
║  Quota resets in: {retry_after}                             ║
║                                                              ║
║  Need more? Upgrade to Enterprise:                          ║
║     → https://raas.mekong.dev/enterprise                     ║
╚══════════════════════════════════════════════════════════════╝
""",
    "enterprise": """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Quota Alert                                             ║
╠══════════════════════════════════════════════════════════════╣
║  You've used {daily_used} commands today.                   ║
║                                                              ║
║  Enterprise tier has unlimited quota.                       ║
║  This alert may indicate a temporary issue.                 ║
║                                                              ║
║  Contact support: support@raas.mekong.dev                   ║
╚══════════════════════════════════════════════════════════════╝
""",
}

RATE_LIMIT_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  Rate Limit Exceeded                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Too many requests in a short period.                       ║
║                                                              ║
║  Please wait {retry_after} before trying again.             ║
║                                                              ║
║  This protects fair usage for all users.                    ║
║  Need higher limits? Contact us:                            ║
║     → https://raas.mekong.dev/enterprise                     ║
╚══════════════════════════════════════════════════════════════╝
"""
