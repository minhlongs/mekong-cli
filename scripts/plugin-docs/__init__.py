"""Plugin Documentation System.

Provides tools for generating, validating, and building plugin documentation.

Usage:
    # Generate docs for a single plugin
    python -m scripts.plugin_docs.generate /path/to/plugin --output docs/plugins/

    # Generate for all plugins
    python -m scripts.plugin_docs.generate --plugins-dir packages/plugins --output docs/plugins/

    # Validate docs
    python -m scripts.plugin_docs.validate docs/plugins/

    # Build all docs with MkDocs
    python -m scripts.plugin_docs.build --serve
"""

__version__ = '1.0.0'
