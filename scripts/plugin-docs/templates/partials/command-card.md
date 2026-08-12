<div class="command-card">

### {{ cmd.name }}

{{ cmd.description }}

{% if cmd.usage %}
```bash
{{ cmd.usage }}
```
{% endif %}

{% if cmd.arguments %}
**Arguments:**
{% for arg in cmd.arguments %}
- `{{ arg.name }}`{% if arg.required %} (required){% endif %}: {{ arg.description }}
{% endfor %}
{% endif %}

{% if cmd.options %}
**Options:**
{% for opt in cmd.options %}
- `--{{ opt.name }}`: {{ opt.description }}
{% endfor %}
{% endif %}

{% if cmd.deprecated %}
> ⚠️ **Deprecated:** {{ cmd.deprecationMessage }}
{% endif %}

</div>
