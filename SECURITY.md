# Security Policy

> **POC Notice:** This is a proof-of-concept demonstration repository, not a production
> system. It does not store real credentials, real PII, or live infrastructure secrets.
> Security reports are still welcome and will be addressed promptly.

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Report privately via GitHub Security Advisories:
[https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/security/advisories/new](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/security/advisories/new)

We operate a **90-day coordinated disclosure window**. After 90 days from your initial
report (or sooner if a fix is released), the vulnerability may be disclosed publicly.

## Scope

### In scope
- Hardcoded secrets or credentials checked into the repository
- Insecure defaults in Bicep/IaC modules that would apply to a real deployment
- Dependency vulnerabilities with a known CVE in `requirements.txt` or `requirements-dev.txt`
- Logic errors in compliance code (CTR/SAR thresholds, PII masking) that could mislead a real implementation
- CI/CD workflow permissions that grant excessive access

### Out of scope
- The synthetic data generators themselves (they intentionally use `random` for test data)
- Missing features not yet implemented in the POC
- Issues that only reproduce inside a live Azure/Fabric environment you do not have access to
- Documentation typos

## Supported Versions

| Branch / Tag | Supported |
|---|---|
| `main` (latest) | Yes |
| All prior releases | Best effort |

## Response Timeline

| Stage | Target |
|---|---|
| Initial acknowledgement | 48 hours |
| Triage and severity classification | 5 business days |
| Fix or workaround available | 90 days |
| Public disclosure | 90 days (or sooner with reporter agreement) |
