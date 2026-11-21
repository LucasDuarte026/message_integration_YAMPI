## Summary

Describe what changed, which module(s) were touched, and why.

- **Branch Type:** `feature/*` | `hotfix/*` | `docs/*` (never commit directly to `main`)
- **Related Issue / Spec:** `#` or `REQ-XX` / `ADR-XX`

---

## Type of Change

- [ ] `feat`: New backward-compatible feature (`MINOR`)
- [ ] `fix`: Bug fix or hardening (`PATCH`)
- [ ] `refactor`: Code cleanup without behavior change
- [ ] `docs`: Documentation / SDD update
- [ ] `chore`: Build, CI/DevSecOps, dependencies, or release bump

---

## Verification & Governance Checklist

### 1. Automated Tests & SDD Zero Doc-Drift
- [ ] Ran full test suite: `./.venv/bin/python -m pytest` (all tests pass)
- [ ] Updated module `README.md` (`src/domain/`, `src/core/`, `src/ports/`, `src/workers/`, or `scripts/`) if code inside those directories changed
- [ ] All Markdown links use portable relative paths (no `file://` URIs or local `/home/...` paths)

### 2. DevSecOps Gate & LGPD Compliance
- [ ] Ran `make security-audit` (TruffleHog + Semgrep + Trivy + SkillSpector) with zero critical findings
- [ ] Verified no secrets, `.env` values, API tokens, or DSNs were staged
- [ ] Verified LGPD Zero-PII compliance (`send_default_pii=False`, `_mask_email()`, sanitized exception scopes)
- [ ] Verified PostgreSQL queries use parameterized `%s` placeholders
