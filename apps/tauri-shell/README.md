# @mekong/tauri-shell

macOS desktop shell wrapping the B1 `apps/ide-ui` Next.js static export as a native DMG. Built with Tauri 2.x.

## Architecture

```
apps/tauri-shell/          ← this package
  src-tauri/
    tauri.conf.json        ← points frontendDist → ../ide-ui/out
    Cargo.toml             ← mekong-shell crate, Tauri 2
    src/main.rs            ← entry point
    src/lib.rs             ← Tauri builder + command stubs
    icons/icon.png         ← 512×512 placeholder (replace pre-launch)
apps/ide-ui/               ← B1 Next.js app, must be built first
  out/                     ← static export consumed by Tauri
```

## Prerequisites

- **Rust stable** (`rustup update stable`)
- **Xcode Command Line Tools** (`xcode-select --install`)
- **Node.js 20+** + **pnpm 9+**
- **Tauri CLI 2.x** (installed via devDependencies)

Verify toolchain:

```bash
rustc --version      # >= 1.77
cargo --version
xcodebuild -version  # Xcode 15+ recommended for macOS 14 SDK
```

## Dev Mode (loads localhost:3000)

Run the B1 IDE UI dev server first, then launch Tauri in dev mode:

```bash
# Terminal 1 — start ide-ui dev server
pnpm --filter @mekong/ide-ui dev

# Terminal 2 — start Tauri shell (loads http://localhost:3000)
pnpm --filter @mekong/tauri-shell dev
# or from this directory:
pnpm tauri dev
```

## Production Build (DMG)

Build the B1 static export first, then compile the Tauri shell:

```bash
# Step 1 — build ide-ui static export
pnpm --filter @mekong/ide-ui build
# Output: apps/ide-ui/out/

# Step 2 — build DMG (run on M1/M2/M3 Mac)
pnpm --filter @mekong/tauri-shell build
# or from this directory:
pnpm tauri build
```

### DMG output path

```
apps/tauri-shell/src-tauri/target/release/bundle/dmg/Mekong IDE_0.1.0_aarch64.dmg
```

For universal binary (Intel + Apple Silicon):

```bash
pnpm tauri build --target universal-apple-darwin
# Output: src-tauri/target/universal-apple-darwin/release/bundle/dmg/*.dmg
```

## Install from DMG

1. Open the `.dmg` file
2. Drag **Mekong IDE** to `/Applications`
3. On first launch: right-click → **Open** (Gatekeeper bypass for unsigned app)
4. App loads the bundled `ide-ui/out/` static files — no internet required

## Known Limitations

| Limitation | Status | Plan |
|---|---|---|
| Unsigned DMG | Gatekeeper shows warning | Notarization post-launch ($99/yr Apple Developer) |
| No auto-updater server | `updater.active = false` in conf | Wire endpoint after launch |
| Placeholder icon | Solid teal 512×512 | Replace with production icon pre-launch |
| No code signing | Build works, distribution restricted | Apple Developer account needed |

## Build on M1 Max (remote)

```bash
ssh m1max-cf 'cd /Users/macbook/mekong-cli && pnpm --filter @mekong/ide-ui build && pnpm --filter @mekong/tauri-shell build'
```

CI note: `cargo check` is verified in CI. Full `tauri build` (DMG) requires macOS runner with Xcode — not run in standard CI to avoid cost. Run manually on M1 Max.

## Cargo check (fast verification)

```bash
cd apps/tauri-shell/src-tauri && cargo check
```

Expected: `Finished` with 0 errors, 0 warnings.
