# AGENTS.md

## Scope

This folder is the separate React + TypeScript frontend for the Aether Glimpse
Admin Control Panel.

## Boundaries

- Do not import code from `glimpse/src/`.
- Do not access the database from the frontend.
- Do not generate access tokens or access-link URLs in React.
- The frontend displays API responses and sends form actions to `admin_backend`.
- Keep visual style consistent with Glimpse: warm off-white background, green
  text, lime accent, soft translucent panels, Inter/system sans fonts.

## Current structure

- `src/App.tsx` contains the first operational admin screen.
- `src/api/adminClient.ts` is the only API client.
- `src/types.ts` mirrors admin API response shapes.
- `src/styles.css` contains the local admin visual system.

## Extension points

- The `#dashboard` panel is reserved for the future admin-level dashboard.
- Add new dashboard API calls in `src/api/adminClient.ts`.
- Add new dashboard types in `src/types.ts`.
- Keep dashboard UI separate from enterprise/pilot/link controls.

## Validation

Run from `admin/`:

```bash
npm run test
npm run build
```

