# Browser Hardening and CSRF Alignment

This document records the shipped M1-04 closure.

## Browser hardening headers
All JSON API responses and static frontend responses now include:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Content-Security-Policy` locked to self-hosted app assets and same-origin connections

## CSP posture
Current policy:
- default source restricted to self
- scripts restricted to self
- styles restricted to self plus inline styles already used by the no-build frontend
- images restricted to self and data URLs
- connections restricted to same origin
- frames/objects disabled

## CSRF posture
- explicit-auth mutating routes still require `X-CSRF-Token`
- trusted-local mode continues to bypass CSRF only under the explicit single-user trusted-tailnet exception
- non-loopback trusted-local startup now requires explicit `HCC_TRUST_TAILNET_ONLY=1`

## Scope note
This closes the current M1 browser-hardening alignment for the shipped minimal frontend/runtime posture.
