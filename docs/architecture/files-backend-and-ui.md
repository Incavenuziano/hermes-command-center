# M4-05 / M4-06 — Safe files/workspace backend and files browser UI

## Backend
- `GET /ops/files`
- rooted to Hermes workspace directory
- exposes only normalized file metadata and text previews
- no write/mutate actions are enabled

## UI
- `GET /files`
- dedicated Files Page with workspace listing + detail panel

## Notes
The surface is intentionally read-only and workspace-scoped as a safe precursor to any future file actions.
