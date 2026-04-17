# Release Checklist

## Release Readiness
- [ ] full backend/frontend regression suite passes
- [ ] security audit route reports pass/warn without regressions
- [ ] performance budget snapshot reviewed
- [ ] export/restore round-trip validated
- [ ] load smoke route reports zero failures
- [ ] operator deployment/incident guide reviewed

## Demo Scope
- dashboard, chat, approvals, agents, cron, activity, processes, terminal policy
- memory, skills, files, profiles, channels
- release hardening routes: security audit, performance, export/restore, load smoke

## Release Hygiene
- update backlog alignment and next-issues docs
- commit and push with passing test suite
- keep branch state clean after release prep
