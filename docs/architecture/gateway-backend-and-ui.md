# M4-09 / M4-10 — Gateway/channels backend status with redaction and channels UI

## Backend
- `GET /ops/gateway`
- exposes gateway transport/status and channels list
- secrets and tokens are redacted before leaving the backend

## UI
- `GET /channels`
- dedicated Channels Page with gateway/channel list + detail drill-down

## Notes
This milestone provides operational visibility into delivery surfaces without leaking bearer secrets into the UI.
