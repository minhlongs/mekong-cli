{% extends "base.md" %}

{% block content %}
# API Reference

{% if api.classes or api.functions %}
{% if api.classes and api.classes|length > 0 %}
## Classes

{% for cls in api.classes %}
### {{ cls.name }}

{{ cls.docstring }}

{% if cls.methods and cls.methods|length > 0 %}
#### Methods

{% for method in cls.methods %}
##### {{ method.name }}({{ method.args|join(', ') }})

{{ method.docstring }}
{% endfor %}
{% endif %}
{% endfor %}
{% endif %}

{% if api.functions and api.functions|length > 0 %}
## Functions

{% for func in api.functions %}
### {{ func.name }}({{ func.args|join(', ') }})

{{ func.docstring }}
{% endfor %}
{% endif %}
{% else %}
No API documentation available. The plugin may not expose a programmatic API.
{% endif %}

## Command Handlers

The following command handlers are defined:

{% if plugin.commands %}
{% for cmd in plugin.commands %}
- **{{ cmd.name }}** → `{{ cmd.handler }}`
{% endfor %}
{% else %}
No commands defined.
{% endif %}
{% endblock %}
