# AGENTS.md

## Scope

This package is the separate backend for the Aether Glimpse Admin Control Panel.
It must stay separate from the existing Glimpse coaching backend in `backend/`.

## Boundaries

- Admin backend code lives in `admin_backend/`.
- Admin frontend code lives in `admin/`.
- Glimpse coaching backend code lives in `backend/`.
- Shared database instance is allowed.
- Admin tables must remain logically separate from Glimpse session/state tables.
- Do not put admin business logic into React components.
- Do not put admin routes into `backend/api.py` unless explicitly asked.

## Runtime contracts

- All `/admin/*` routes require admin authentication.
- `/access/validate` is intentionally not admin-authenticated; the token itself
  is the credential being validated.
- Access tokens are external secrets. Store and log only safe prefixes outside
  authorised admin responses.
- `pilot_id` is the stable context stored on telemetry. Tokens are not tenant IDs.

## Files

- `app.py` owns the FastAPI app object and CORS for the admin app.
- `routes.py` owns HTTP routes and error mapping.
- `service.py` owns business operations and link generation.
- `repository.py` owns SQL access.
- `models.py` owns admin API contracts.
- `security.py` owns simple admin auth.

## Validation

Run:

```bash
python -m unittest tests.test_admin_backend
python admin_smoke_test.py
```

If token validation or telemetry association changes, also run the existing
Glimpse smoke and telemetry tests.

