# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in stripewrap, please report it
responsibly by emailing **edwin.three@icloud.com** with the subject line
`[SECURITY] stripewrap vulnerability report`.

Please include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Impact assessment** — what an attacker could achieve
4. **Suggested fix** (if you have one)

### What to Expect

- **Acknowledgment** within 48 hours of your report
- **Status update** within 7 days with an assessment and timeline
- **Credit** in the release notes (unless you prefer to remain anonymous)

### Scope

The following are in scope for security reports:

- Webhook signature verification bypass
- API key exposure through logging or error messages
- Injection vulnerabilities in request construction
- Dependency vulnerabilities that affect stripewrap users

### Out of Scope

- Vulnerabilities in Stripe's own API or infrastructure
- Issues that require physical access to the user's machine
- Social engineering attacks

## Security Best Practices for Users

When using stripewrap in your applications:

1. **Never hardcode API keys** — use environment variables or a secrets manager
2. **Use test keys** (`sk_test_...`) during development
3. **Always verify webhook signatures** using `construct_event()` — never trust
   raw payloads
4. **Keep stripewrap updated** to receive security patches
5. **Restrict API key permissions** using Stripe's restricted keys feature
