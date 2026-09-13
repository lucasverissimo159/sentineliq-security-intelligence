# Auth example

Create a JWT token for a protected API call with a subject and scopes.

```python
from sentineliq.infrastructure.security.jwt_auth import create_access_token

token = create_access_token("operator@example.com", scopes=["logs:write", "alerts:read"])
print(token)
```

Expected header:

```http
Authorization: Bearer <token>
```
