{% extends "base.md" %}

{% block content %}
## Overview

{{ plugin.description }}

{% if plugin.homepage %}
**Homepage:** {{ plugin.homepage }}
{% endif %}

{% if plugin.repository %}
**Repository:** {{ plugin.repository.url if plugin.repository.url else plugin.repository }}
{% endif %}

## Features

{% if plugin.keywords and plugin.keywords|length > 0 %}
**Keywords:** {{ plugin.keywords|join(', ') }}
{% endif %}

## Installation

```bash
mekong plugin install {{ plugin.id }}
```

{% if plugin.permissions and plugin.permissions|length > 0 %}
## Permissions

This plugin requires the following permissions:

{% for perm_type, perm_list in plugin.permissions.items() %}
- **{{ perm_type }}**: {{ perm_list|join(', ') }}
{% endfor %}
{% endif %}

{% if plugin.commands and plugin.commands|length > 0 %}
## Commands

This plugin provides {{ plugin.commands|length }} command(s):

{% for cmd in plugin.commands %}
- **{{ cmd.name }}**: {{ cmd.description }}
{% endfor %}

See [Commands Reference](commands.md) for full details.
{% endif %}

## Configuration

{% if plugin.config and plugin.config.schema %}
See [Configuration Reference](config.md) for available settings.
{% else %}
This plugin does not require configuration.
{% endif %}

## API Reference

See [API Reference](api.md) for detailed API documentation.

{% if plugin.troubleshooting %}
## Troubleshooting

{% for issue in plugin.troubleshooting %}
### {{ issue.symptom }}

{{ issue.cause }}

**Solution:** {{ issue.solution }}
{% endfor %}
{% endif %}

## Changelog

{% if plugin.changelog %}
{{ plugin.changelog }}
{% else %}
No changelog available.
{% endif %}

## See Also

- [Commands Reference](commands.md)
- [API Reference](api.md)
- [Configuration](config.md)
{% endblock %}
