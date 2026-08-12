{% extends "base.md" %}

{% block content %}
# Commands Reference

{% if commands and commands|length > 0 %}
This plugin provides {{ commands|length }} command(s).

{% for cmd in commands %}
## {{ cmd.name }}

{{ cmd.description }}

{% if cmd.usage %}
**Usage:** `{{ cmd.usage }}`
{% endif %}

{% if cmd.arguments and cmd.arguments|length > 0 %}
### Arguments

{% for arg in cmd.arguments %}
- `{{ arg.name }}` {% if arg.required %}(required){% endif %}: {{ arg.description }}
{% endfor %}
{% endif %}

{% if cmd.options and cmd.options|length > 0 %}
### Options

{% for opt in cmd.options %}
- `--{{ opt.name }}` {% if opt.alias %}(`-{{ opt.alias }}`){% endif %}: {{ opt.description }}
{% if opt.default %}Default: `{{ opt.default }}`{% endif %}
{% endfor %}
{% endif %}

{% if cmd.deprecated %}
> ⚠️ **Deprecated:** {{ cmd.deprecationMessage if cmd.deprecationMessage else 'This command is deprecated.' }}
{% endif %}

---
{% endfor %}
{% else %}
This plugin does not provide any commands.
{% endif %}
{% endblock %}
