# Security Policy

KIROSHI is designed with a defense-in-depth, privacy-first engineering philosophy.

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## Reporting a Vulnerability

If you discover a security vulnerability in the KIROSHI platform, please do **NOT** file a public issue. Instead, report it privately to the project maintainers:

- **Primary Contact:** security@kiroshi.dev / maintainer team
- **PGP Key:** (Configured for production deployments)

Please include in your report:
1. Description of the vulnerability.
2. Steps to reproduce or proof-of-concept exploit.
3. Potential impact on user data or system integrity.
4. Suggested remediation if available.

We commit to acknowledging reports within 48 hours and providing a remediation timeline within 7 days.

---

## Security Guarantees & Architecture (v0.1)

1. **Authentication & Password Storage**:
   - Passwords hashed using bcrypt with salt rounds >= 12.
   - Cryptographic access tokens using HMAC-SHA256 (HS256) or RS256 with strict expiration.
2. **Access Control**:
   - Explicit server-enforced role-based access control (RBAC).
   - Insecure Direct Object Reference (IDOR) prevention: Tourists cannot access or mutate records belonging to other users.
3. **Data Protection**:
   - Zero hardcoded secrets: all credentials loaded from environment variables.
   - `.env`, `.venv`, database binaries, and sensitive caches are strictly ignored in version control.
   - PII is not exposed to third parties or untrusted roles.
