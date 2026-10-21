# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License, Offline, and Network Error Message Templates — ROIaaS Phase 6b."""

FREE_TIER_UPGRADE_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  💎 Unlock Pro Features                                      ║
╠══════════════════════════════════════════════════════════════╣
║  You're on the Free tier (10 commands/day).                 ║
║                                                              ║
║  Upgrade to Pro for:                                         ║
║  ✅ 1000 commands/day (100x more)                           ║
║  ✅ Premium agents (Swarm, Schedule, Telegram)              ║
║  ✅ Priority support                                        ║
║  ✅ Advanced analytics                                      ║
║                                                              ║
║  🎯 Special offer: First month 50% off                      ║
║     → https://raas.mekong.dev/pricing                        ║
╚══════════════════════════════════════════════════════════════╝
"""

LICENSE_REVOKED_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🔒  License Revoked                                         ║
╠══════════════════════════════════════════════════════════════╣
║  Your license key has been revoked.                         ║
║                                                              ║
║  Access to premium features is blocked.                     ║
║                                                              ║
║  Possible reasons:                                           ║
║  • Terms of Service violation                               ║
║  • Payment issue                                            ║
║  • Account suspension                                       ║
║                                                              ║
║  📞 Contact support to appeal:                              ║
║     → support@raas.mekong.dev                               ║
║     → https://raas.mekong.dev/support                        ║
╚══════════════════════════════════════════════════════════════╝
"""

LICENSE_EXPIRED_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  ⏰  License Expired                                         ║
╠══════════════════════════════════════════════════════════════╣
║  Your license expired on {expiry_date}.                     ║
║                                                              ║
║  Access to premium features is blocked.                     ║
║                                                              ║
║  🔄 Renew your license to continue:                         ║
║     → https://raas.mekong.dev/pricing                        ║
║                                                              ║
║  Need help? Contact us:                                     ║
║     → support@raas.mekong.dev                               ║
╚══════════════════════════════════════════════════════════════╝
"""

OFFLINE_GRACE_PERIOD_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  📡  Offline Mode Activated                                  ║
╠══════════════════════════════════════════════════════════════╣
║  Remote validation unavailable.                             ║
║  Using cached license state (grace period).                 ║
║                                                              ║
║  ⏳ Grace period remaining: {remaining_hours} hours       ║
║                                                              ║
║  Commands allowed during grace period.                      ║
║                                                              ║
║  💡 Restore connectivity to re-validate license.            ║
╚══════════════════════════════════════════════════════════════╝
"""

GRACE_PERIOD_EXPIRED_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  📡  Offline Grace Period Expired                            ║
╠══════════════════════════════════════════════════════════════╣
║  Your 24-hour offline grace period has expired.             ║
║                                                              ║
║  Network connection required to validate license.           ║
║                                                              ║
║  Please connect to the internet and try again.              ║
║                                                              ║
║  Having issues? Contact support:                            ║
║     → support@raas.mekong.dev                               ║
╚══════════════════════════════════════════════════════════════╝
"""

NETWORK_ERROR_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🌐  Network Error                                           ║
╠══════════════════════════════════════════════════════════════╣
║  Cannot reach license server.                               ║
║                                                              ║
║  Error: {error_message}                                      ║
║                                                              ║
║  Check your internet connection and try again.              ║
║                                                              ║
║  If the problem persists:                                   ║
║     → https://raas.mekong.dev/status                        ║
║     → support@raas.mekong.dev                               ║
╚══════════════════════════════════════════════════════════════╝
"""

JWT_ERROR_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🔑  JWT License Error                                       ║
╠══════════════════════════════════════════════════════════════╣
║  {message}                                                   ║
║                                                              ║
║  JWT tokens are cryptographically signed and verified       ║
║  offline - no network required.                             ║
║                                                              ║
║  Get a new JWT token:                                        ║
║     → mekong license generate --tier {tier}                  ║
║     → https://raas.mekong.dev/pricing                        ║
╚══════════════════════════════════════════════════════════════╝
"""

LICENSE_ERROR_TEMPLATE = """
╔══════════════════════════════════════════════════════════════╗
║  🔒  License Error                                           ║
╠══════════════════════════════════════════════════════════════╣
║  {message}                                                   ║
║                                                              ║
║  Command '{command}' requires a valid license.               ║
║                                                              ║
║  Get your license key:                                       ║
║     → https://raas.mekong.dev/pricing                        ║
║                                                              ║
║  Already have a key? Check with:                            ║
║     mekong license status                                    ║
╚══════════════════════════════════════════════════════════════╝
"""
