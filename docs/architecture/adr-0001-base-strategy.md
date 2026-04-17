# ADR-0001 — Base Strategy

## Status
Accepted

## Decision
Hermes Command Center will not be implemented as a direct fork of openclaw-mission-control, and will not ship as an unmodified hermes-webui.

Instead it will use a hybrid strategy:
- mission-control UX and control-plane breadth inspired by openclaw-mission-control
- Hermes-native operational semantics and pragmatic integration lessons inspired by hermes-webui
- new backend contracts and security posture tailored to Hermes

## Rationale
This preserves product ambition while avoiding over-coupling to non-Hermes runtime assumptions and unnecessary frontend complexity.
