# API Integration Guide

> **Info:** This guide covers the REST API v2. For v1 documentation, see the legacy docs.

## Authentication

All API requests require a Bearer token. Generate one from your [account settings](/settings/api-keys).

```bash
curl -X POST https://api.example.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "***"}'
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v2/users | List all users |
| POST | /api/v2/users | Create a new user |
| GET | /api/v2/users/:id | Get user by ID |

## Rate Limits

> **Warning:** Exceeding rate limits will result in a 429 response. Implement exponential backoff.

- Standard tier: 100 requests/minute
- Pro tier: 1,000 requests/minute
- Enterprise: Custom limits

### Response Codes

1. **200** - Success
1. **401** - Unauthorized (check your token)
1. **429** - Rate limited (back off and retry)
1. **500** - Server error (contact support)

> **Tip:** Use the `X-RateLimit-Remaining` header to monitor your usage before hitting limits.
