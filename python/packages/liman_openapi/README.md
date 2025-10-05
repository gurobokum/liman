# Liman OpenAPI plugin

[![codecov](https://codecov.io/gh/gurobokum/liman/graph/badge.svg?token=PMKWXNBF1K&component=python/liman_openapi)](https://codecov.io/gh/gurobokum/liman?components[0]=python/liman_openapi)

Allows to generate ToolNode based on OpenAPI specification.

```python
spec = load_openapi(file_path) # or url, yaml, json
registry = Registry()

tool_nodes = create_tool_nodes(spec, registry)
```

## Limitations

- Not supported securitySchemes:
  - [] OpenID
  - [] OAuth2
