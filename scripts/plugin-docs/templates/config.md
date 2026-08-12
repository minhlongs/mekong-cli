{% extends "base.md" %}

{% block content %}
# Configuration

{% if config and config.schema %}
## Configuration Schema

{{ config.description if config.description else 'This plugin can be configured via environment variables or a configuration file.' }}

{% if config.schema.properties %}
### Available Settings

{% for prop_name, prop_def in config.schema.properties.items() %}
#### {{ prop_name }}

{% if prop_def.description %}
{{ prop_def.description }}
{% endif %}

- **Type:** {{ prop_def.type if prop_def.type else 'any' }}
{% if prop_name in config.defaults %}**Default:** `{{ config.defaults[prop_name] }}`{% endif %}
{% if prop_def.required %}**Required:** Yes{% endif %}
{% endfor %}
{% endif %}
{% else %}
This plugin does not have configurable settings.
{% endif %}

## Environment Variables

Plugin configuration can be provided via environment variables:

```
MEKONG_PLUGIN_{{ plugin.id|upper }}_<SETTING_NAME>=value
```

For example:

```
MEKONG_PLUGIN_{{ plugin.id|upper }}_API_KEY=your_api_key
```
{% endblock %}
