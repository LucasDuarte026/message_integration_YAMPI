# Security Policy

## Supported Versions

Only the latest stable release series receives active security patches, dependency updates, and DevSecOps gate verification.

| Version | Supported | Notes |
| :--- | :---: | :--- |
| `7.0.x` | :white_check_mark: | Current official production release (Major v7.0.0 launch) |
| `6.8.x` | :warning: | Maintenance / upgrade to `7.0.x` recommended |
| `< 6.8.0` | :x: | End of life — no longer maintained |

---

## Automated 4-Layer DevSecOps Controls

This repository enforces defense-in-depth security controls prior to commits and pushes via [`scripts/security_audit.sh`](./scripts/security_audit.sh) and `Makefile` targets:

1. **Secret Scanning (`TruffleHog` — `make security-secrets`)**: Inspects recent Git commit history and working-tree files for verified secrets, API keys, and private credentials.
2. **Static Application Security Testing (`Semgrep` — `make security-sast`)**: Runs `p/python`, `p/flask`, and `p/secrets` rulesets across `src/` and `scripts/` in blocking mode.
3. **Supply-Chain & Container Hardening (`Trivy` — `make security-infra`)**: Scans `requirements.txt` for `HIGH`/`CRITICAL` CVEs and audits `Dockerfile`, `docker-compose.yml`, and `docker-compose.prod.yml` for misconfigurations.
4. **AI Agent Skill Auditing (`SkillSpector` — `make security-skills`)**: Audits bundled agent skills under `.agents/skills/` against prompt injection, data exfiltration, and unsafe tool patterns.

Run the complete local verification suite before submitting a pull request:

```bash
make security-audit
```

---

## Data Privacy & LGPD Zero-PII Guarantee

- **Telemetry Scrubbing**: Sentry SDK is initialized with `send_default_pii=False` (`src/core/logging_config.py`).
- **Local Variable Redaction**: `_build_pii_sanitizer_processor` (`src/core/telemetry.py`) recursively scrubs sensitive keys (`email`, `raw_email`, `customer_data`, `order_data`, `cart_data`, `cpf`, `pix_code`, `html_body`, and auth/token/secret fields) from `frame["vars"]` and exception scopes before leaving the host.
- **Email Masking & Domain-Only Metrics**: Operational logs mask recipient addresses via `_mask_email()`, while Sentry Application Metrics only record the recipient domain (`email.recipient_domain`).
- **SQL Injection Prevention**: All PostgreSQL operations in `src/ports/postgres_repo.py` strictly use parameterized queries (`%s`).

---

## Reporting a Vulnerability

**Do not disclose security vulnerabilities publicly in GitHub Issues or Pull Requests.**

If you discover a vulnerability, secret exposure, or LGPD/PII leak vector:

1. **GitHub Private Vulnerability Reporting**: Navigate to the **Security** tab of this repository and select **Report a vulnerability** (preferred private channel).
2. **Direct Maintainer Contact**: Contact the repository maintainers privately with:
   - Affected component (`Orders STG`, `Carts STC`, `SMTP Provider`, `PostgreSQL Repo`, `Webhook Server`, or `Telemetry`).
   - Reproduction steps or proof of concept (with all real customer data and credentials redacted).
   - Impact assessment and suggested remediation, if known.

We aim to acknowledge reports within **48 hours** and deliver a validated patch with a regression test on the active `7.0.x` line.
