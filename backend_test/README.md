# Coach V3 Test Backend

Standalone FastAPI backend for local frontend testing.

It is intentionally separate from `backend/`, returns static JSON, ignores user
input, waits one second before each main response, and never calls AI models.

## Run locally

```bash
uvicorn backend_test.main:app --reload --port 8001
```

Then point the React frontend API base URL at:

```text
http://127.0.0.1:8001
```

## Routes

- `POST /problem`
- `POST /coach`
- `POST /synthesis`
- `POST /pathways`
- `GET /session_initialise`
- `POST /user_message`
- `GET /health`
