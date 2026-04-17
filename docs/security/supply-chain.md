# Hermes Command Center — Supply Chain Policy

## Goals

Reduce risk from compromised dependencies, accidental secret commits, and unsafe release practices.

## Dependency policy

- every new dependency requires explicit justification in the PR
- avoid adding dependencies for cosmetic or marginal convenience features
- prefer standard library or existing project dependencies when reasonable
- frontend dependency additions should be reviewed with special skepticism

## Lockfiles

- lockfiles must be committed
- CI must fail if lockfiles are missing or stale relative to manifests
- generated dependency state must remain reproducible

## Automated checks

CI should include:
- dependency vulnerability scanning
- secret scanning
- static checks for baseline project health

Recommended tools:
- `pip-audit` for Python
- `npm audit` or equivalent for JavaScript/Node
- `gitleaks` or equivalent for secret scanning

## Release hygiene

Before release:
- review dependency graph changes
- generate SBOM (CycloneDX or SPDX)
- review critical/high severity dependency findings
- review that no secrets or machine-local config files are included

## Signing and provenance

Preferred posture:
- signed tags for releases
- provenance or signed release artifacts where practical
- document release process in a dedicated release checklist

## Examples and templates

- never ship real secrets in examples
- example config must be clearly non-functional until edited by user
- documentation must distinguish placeholder values from real credentials

## Emergency response

If a dependency compromise is suspected:
- freeze releases
- identify affected versions
- cut a mitigation patch or rollback release
- document operator guidance in release notes / SECURITY guidance
