# Plugin System Release Notes

> **Current Version:** 1.0.0 | **Date:** 2026-06-20

This document tracks the evolution of the Mekong CLI plugin system and documentation.

---

## v1.0.0 (2026-06-20) — Plugin Documentation System Launch

### Added

- **Plugin Documentation System** - Automatic generation of plugin documentation from manifests
  - CLI generator: `scripts/plugin-docs/generate.py`
  - Batch builder: `scripts/plugin-docs/build.py`
  - Linter: `scripts/plugin-docs/validate.py`
  - Pre-commit hook: `scripts/plugin-docs/validate-changed.py`
  - Templates: Jinja2-based, fully customizable
  - CI/CD integration: GitHub Actions workflow
  - Documentation: Complete guides and API reference

- **Plugin Manifest Schema** - Hardened v1 schema with:
  - Required fields: `id`, `name`, `version`, `entrypoint`
  - Command definitions with arguments, options, examples
  - Permission system
  - Configuration schema
  - Hook and event registrations

- **Plugin SDK** - Python SDK for plugin development (`packages/mekong-plugin-sdk/`)
  - `MekongPlugin` base class
  - `PluginContext` for runtime services
  - `CommandRegistry` for command registration
  - `HookRegistry` and `EventBus`
  - Type-safe manifest dataclasses

- **Sample Plugin** - Benchmark test plugin with complete manifest

### Changed

- Plugin system moved from experimental to **Production Ready**
- All plugin documentation auto-generated from manifests
- Standardized plugin directory layout

### Fixed

- Plugin validation no longer fails on optional fields
- Generator handles missing optional manifest fields gracefully

---

## v0.9.0 (2026-05-15) — Plugin System Beta

### Added

- Plugin discovery from `packages/` directory
- Basic plugin loading and registration
- Command Fabric integration
- Unified MCU billing for plugins
- Backward compatibility layer for legacy commands

### Changed

- Refactored `plugin_loader.py` for better performance
- Improved security validation (dangerous imports, secrets)

---

## v0.8.0 (2026-04-01) — Plugin Architecture

### Added

- Initial plugin architecture specification
- Plugin manifest format (v0)
- PluginRegistry with lifecycle management
- PluginValidator with security scanning
- MarketplaceClient for remote plugin discovery

### Notes

This was the first public release of the plugin system design.

---

## Upcoming (Planned)

### v1.1.0 (TBD)

- [ ] Multi-language support (TypeScript/JavaScript plugins)
- [ ] Worker/process isolation modes
- [ ] Signature verification for published plugins
- [ ] Hot module reloading in development
- [ ] Plugin marketplace web interface
- [ ] Versioned documentation (multiple plugin versions)

### v1.2.0 (TBD)

- [ ] Plugin dependency resolution
- [ ] Plugin upgrade/rollback commands
- [ ] Plugin health monitoring dashboard
- [ ] Advanced permission system with fine-grained controls
- [ ] Plugin sandboxing improvements (WASM support)

---

## Migration Guides

### From v0.x to v1.0.0

1. Update `plugin.json` to include all required fields
2. Use `mekong_plugin_sdk` base classes instead of custom implementations
3. Move command handlers to separate module (e.g., `handlers.py`)
4. Add documentation in Python docstrings for auto-generation

See [Plugin Migration Guide](plugin-migration-guide.md) for detailed steps.

---

## Compatibility

| Mekong CLI Version | Plugin System Version |
|--------------------|----------------------|
| ^6.0.0 | ^1.0.0 |
| ^5.0.0 | ^0.9.0 |
| <5.0.0 | Not supported |

---

## Plugin System Versioning

The plugin system follows [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes to manifest format or SDK API
- **Minor**: New features with backward compatibility
- **Patch**: Bug fixes, documentation improvements

---

## Support

- Documentation: https://docs.mekongmind.com/plugins
- Discord: `#plugins` channel
- GitHub Issues: <https://github.com/mekongcli/mekong-cli/issues>
