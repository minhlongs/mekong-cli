# Plugin System Contracts

Machine-readable contracts and schemas for the Mekong CLI Plugin System.

## Contents

- `plugin-manifest-schema.json` - JSON Schema for plugin manifest files (plugin.json)
- `plugin-api-types.json` - TypeScript type definitions for plugin API (generated)
- `contracts.yaml` - OpenAPI contracts for plugin-related APIs

## Usage

### Validating Plugin Manifests

```bash
# Using ajv-cli
ajv validate -s plugin-manifest-schema.json -d ../plugins/my-plugin/plugin.json

# Using Python
python3 -c "
import json, jsonschema
schema = json.load(open('plugin-manifest-schema.json'))
manifest = json.load(open('../plugins/my-plugin/plugin.json'))
jsonschema.validate(manifest, schema)
"
```

### Generating TypeScript Types

```bash
# Generate TypeScript interface from schema
json2ts -i plugin-manifest-schema.json -o plugin-api-types.d.ts
```

## Schema Version

Current schema version: `v1.0.0`

Schema ID: `https://mekong.dev/schema/plugin-manifest/v1.json`

## Versioning

Schemas follow semantic versioning. Breaking changes require major version bump.

## Related Documentation

- [Plugin Architecture](../plugin-architecture.md)
- [Plugin Developer Guide](../plugin-developer-guide.md)
- [Plugin Manifest Format Reference](../plugin-manifest-format.md)
