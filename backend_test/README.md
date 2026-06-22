# Coach V3 Test Backend + Glimpse Setup

This test backend lets Glimpse run without the real backend flow or any AI
model calls. It lives in `backend_test/` and is intentionally separate from the
production backend in `backend/`.

The feedback form route reads `backend/config/feedback_forms.yaml` dynamically,
matching the production backend contract. If that YAML is invalid, the test
backend follows production behaviour and returns `show_feedback: false`.
Like production, `/user_message` resolves the Glimpse participant token from
`client_context.access_token`, `accessToken`, or `token`, stores the resolved
`pilot_id` on the session, then `/coach/v2/feedback-form` reads
`admin_pilots.feedback_pack_id` and uses that pack if it exists in YAML.
Otherwise it falls back to `default_feedback_pack_id`. For local static testing,
`pilot_id` can still be supplied as `pilot_id` or `pilotId` inside
`client_context` on `/user_message`.

The Glimpse frontend reads its backend URL from:

```text
glimpse/.env.local
```

The variable is:

```bash
VITE_API_BASE_URL=...
```

After changing `.env.local`, restart the Glimpse dev server. Vite reads env
files only when the dev server starts.

## 1. Desktop Browser

Use this when running Glimpse on your Mac in a desktop browser.

Start the test backend:

```bash
cd /Users/lucadematteis/coachV3
source venv/bin/activate
uvicorn backend_test.main:app --reload --port 8001
```

Set `glimpse/.env.local` to:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001
```

Start Glimpse:

```bash
cd /Users/lucadematteis/coachV3/glimpse
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## 2. Mobile Simulator On Your Mac

Use this when testing the mobile layout in a simulator running on the same Mac.

### iOS Simulator

Start the test backend:

```bash
cd /Users/lucadematteis/coachV3
source venv/bin/activate
uvicorn backend_test.main:app --reload --port 8001
```

Set `glimpse/.env.local` to:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001
```

Start Glimpse:

```bash
cd /Users/lucadematteis/coachV3/glimpse
npm run dev
```

Open Safari in the iOS Simulator and go to:

```text
http://127.0.0.1:5173
```

### Android Emulator

Android emulators usually reach the host Mac through `10.0.2.2`.

Start the test backend so it listens beyond localhost:

```bash
cd /Users/lucadematteis/coachV3
source venv/bin/activate
uvicorn backend_test.main:app --reload --host 0.0.0.0 --port 8001
```

Set `glimpse/.env.local` to:

```bash
VITE_API_BASE_URL=http://10.0.2.2:8001
```

Start Glimpse so the emulator can reach it:

```bash
cd /Users/lucadematteis/coachV3/glimpse
npm run dev -- --host 0.0.0.0
```

Open the emulator browser and go to:

```text
http://10.0.2.2:5173
```

## 3. Actual Mobile Phone

Use this when testing on a real phone connected to the same Wi-Fi network as
your Mac.

Find your Mac's Wi-Fi IP address:

```bash
ipconfig getifaddr en0
```

If that prints nothing, try:

```bash
ipconfig getifaddr en1
```

In the examples below, replace `<MAC_IP>` with that IP address.

Start the test backend so your phone can reach it:

```bash
cd /Users/lucadematteis/coachV3
source venv/bin/activate
uvicorn backend_test.main:app --reload --host 0.0.0.0 --port 8001
```

Set `glimpse/.env.local` to:

```bash
VITE_API_BASE_URL=http://<MAC_IP>:8001
```

Start Glimpse so your phone can reach it:

```bash
cd /Users/lucadematteis/coachV3/glimpse
npm run dev -- --host 0.0.0.0
```

Open your phone browser and go to:

```text
http://<MAC_IP>:5173
```

Example, if your Mac IP is `192.168.1.42`:

```bash
VITE_API_BASE_URL=http://192.168.1.42:8001
```

Then open:

```text
http://192.168.1.42:5173
```

## Switching Between Desktop And Mobile

You can comment out old values in `glimpse/.env.local` instead of deleting
them:

```bash
# Desktop / iOS Simulator
VITE_API_BASE_URL=http://127.0.0.1:8001

# Real phone example
# VITE_API_BASE_URL=http://192.168.1.42:8001
```

Only one uncommented `VITE_API_BASE_URL` line should be active at a time.

## Quick Checks

Check the test backend:

```bash
curl http://127.0.0.1:8001/health
```

Expected response:

```json
{"status":"ok"}
```

For real phone testing, check the backend using your Mac IP:

```bash
curl http://<MAC_IP>:8001/health
```

## Routes

Production-compatible routes used by the current Glimpse client:

- `GET /session_initialise`
- `POST /user_message`
- `GET /coach/v2/feedback-form`
- `POST /coach/v2/feedback`
- `POST /telemetry/session_event`
- `GET /debug_trace/{session_id}`

Production-compatible admin/export route:

- `GET /admin/telemetry/export.xlsx`

Static helper routes:

- `POST /problem`
- `POST /coach`
- `POST /synthesis`
- `POST /pathways`
- `GET /health`
