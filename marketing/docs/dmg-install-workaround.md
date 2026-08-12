# DMG Install Workaround — Unsigned macOS Apps (xattr -cr)

## Problem

When an app is not signed with an Apple Developer ID, macOS Gatekeeper blocks launch.
The `build-dmg.sh` script ships the unsigned build when no developer certificate is found.

## Fix for Early Adopters

Run on each machine before first launch:

    xattr -cr /Applications/MekongCLI.app
    sudo spctl --add --label "MekongCLI-FirstRun" /Applications/MekongCLI.app

## Notarization

Once a Developer ID Application cert is installed, `build-dmg.sh` handles signing
via `productbuild`, notarization via `xcrun notarytool`, and stapling automatically.
