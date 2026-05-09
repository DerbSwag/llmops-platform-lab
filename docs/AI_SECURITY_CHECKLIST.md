# AI Security Checklist

Infrastructure-level security controls for LLM/AI systems. Based on OWASP LLM Top 10.

---

## 1. Input Security

- [x] Prompt injection detection (regex + pattern matching)
- [x] Input length validation (max 4096 chars)
- [x] Encoding validation (UTF-8 only)
- [x] PII filtering before LLM (Thai ID, credit card, email, phone)
- [ ] Content classification (NSFW, harmful)
- [ ] Multi-language injection detection

## 2. Authentication & Authorization

- [x] API key authentication (Bearer token)
- [x] Key hashing (never stored plaintext)
- [ ] Key rotation policy (90-day max)
- [ ] Role-based access (admin, user, readonly)
- [ ] OAuth2 / OIDC integration
- [ ] Per-key model access control

## 3. Rate Limiting & Abuse Prevention

- [x] Token bucket rate limiting per API key
- [x] Configurable RPM (requests per minute)
- [ ] Token-based rate limiting (input + output tokens)
- [ ] IP-based rate limiting
- [ ] Adaptive rate limiting (increase on abuse detection)
- [ ] CAPTCHA for suspicious patterns

## 4. Data Protection

- [x] PII redaction before sending to LLM
- [ ] Data classification labels
- [ ] Encryption at rest (vector DB)
- [ ] Encryption in transit (TLS everywhere)
- [ ] Data retention policy (auto-delete after N days)
- [ ] Audit log for all data access

## 5. Model Security

- [ ] Model access control (who can serve which model)
- [ ] Model integrity verification (checksum)
- [ ] Prevent model theft (no direct model download API)
- [ ] Sandboxed execution environment
- [ ] Output filtering (prevent data leakage)
- [x] Response length limiting

## 6. Monitoring & Incident Response

- [x] Request/response logging (sanitized)
- [x] Cost tracking per API key
- [x] Latency monitoring (P95, P99)
- [x] Error rate alerting
- [x] Budget threshold alerts
- [ ] Anomaly detection on usage patterns
- [ ] Automated key revocation on abuse

## 7. Infrastructure

- [ ] Network segmentation (LLM backend not public)
- [ ] Zero-trust architecture
- [x] Container-based deployment
- [ ] Secrets management (Vault / sealed secrets)
- [ ] Image scanning (Trivy)
- [ ] RBAC on Kubernetes
- [ ] Regular penetration testing

## 8. Compliance

- [ ] OWASP LLM Top 10 assessment
- [ ] ISO 27001 controls mapping
- [ ] Data processing agreement (DPA)
- [ ] AI ethics review
- [ ] Responsible AI documentation
- [ ] Incident response plan for AI-specific threats

---

## Quick Reference: OWASP LLM Top 10

| # | Threat | Our Mitigation |
|---|--------|----------------|
| LLM01 | Prompt Injection | Pattern detection + input validation |
| LLM02 | Insecure Output | Response sanitization |
| LLM03 | Training Data Poisoning | N/A (using pre-trained) |
| LLM04 | Model DoS | Rate limiting + timeout |
| LLM05 | Supply Chain | Image scanning, pinned versions |
| LLM06 | Sensitive Info Disclosure | PII filtering |
| LLM07 | Insecure Plugin Design | Input validation on all endpoints |
| LLM08 | Excessive Agency | Restricted tool access |
| LLM09 | Overreliance | System prompts with caveats |
| LLM10 | Model Theft | Network segmentation |
