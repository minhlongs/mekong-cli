# DMG Signing Pipeline Setup — Report

## What was done

1. **Check for Apple Developer certificate** — `security find-identity -v` returned **0 valid identities**.

2. **Created `docs/dmg-install-workaround.md`** — documents the `xattr -cr` + `spctl` workaround for early adopters installing unsigned DMGs. Covers:
   - Primary fix: clear quarantine attributes + allow override
   - Alternative: translocate-then-allow for macOS 13+
   - Future notarization note (self-explaning once cert is acquired)

3. **Created `scripts/packaging/build-dmg.sh`** with dual-mode behavior:
   - **Always produces** an unsigned DMG (`<vol>-unsigned.dmg`)
   - **Optionally produces** a signed + notarized DMG (`<vol>-signed.dmg`) if a Developer ID Application or Apple Distribution identity is found on the keychain
   - Steps in signed mode: `hdiutil sign --timestamp` → `xcrun notarytool submit --wait` → `xcrun stapler staple`

## Manual steps remaining

| Step | Action |
|------|--------|
| **1** | Obtain Apple Developer ID Application certificate from developer.apple.com |
| **2** | Install cert in macOS Keychain (login chain) |
| **3** | Set `NOTARY_PROFILE` if using a named `notarytool` profile (default: `mekong-notary`) |
| **4** | Add App Store Connect API key for `notarytool` auth: `xcrun notarytool store-credentials <profile> --apple-id ...` |

## Why no cert today

Zero valid signing identities on the development Mac. The pipeline is ready to activate as soon as a Developer ID certificate is enrolled. The unsigned DMG + documented workaround allows early adopter distribution in the interim.
Status: DONE
