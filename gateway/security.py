"""AI Security Layer — Prompt injection detection, input validation, PII filtering."""
import re

# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"disregard\s+(all\s+)?previous",
    r"you\s+are\s+now\s+(?:a|an)\s+",
    r"system\s*:\s*",
    r"<\|im_start\|>",
    r"\[INST\]",
    r"###\s*(system|instruction)",
    r"forget\s+(everything|all)",
    r"new\s+instructions?\s*:",
]

# PII patterns
PII_PATTERNS = {
    "thai_id": r"\b\d{1}-\d{4}-\d{5}-\d{2}-\d{1}\b",
    "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone_th": r"\b0[689]\d{1}-?\d{3}-?\d{4}\b",
}

MAX_INPUT_LENGTH = 4096
MAX_OUTPUT_LENGTH = 8192


class SecurityCheckResult:
    def __init__(self, passed: bool, reason: str = ""):
        self.passed = passed
        self.reason = reason


def check_prompt_injection(text: str) -> SecurityCheckResult:
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return SecurityCheckResult(False, f"Prompt injection detected: {pattern}")
    return SecurityCheckResult(True)


def check_input_validation(text: str) -> SecurityCheckResult:
    if not text or not text.strip():
        return SecurityCheckResult(False, "Empty input")
    if len(text) > MAX_INPUT_LENGTH:
        return SecurityCheckResult(False, f"Input too long ({len(text)} > {MAX_INPUT_LENGTH})")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return SecurityCheckResult(False, "Invalid encoding")
    return SecurityCheckResult(True)


def filter_pii(text: str) -> str:
    filtered = text
    for pii_type, pattern in PII_PATTERNS.items():
        filtered = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", filtered)
    return filtered


def run_security_checks(text: str) -> SecurityCheckResult:
    validation = check_input_validation(text)
    if not validation.passed:
        return validation
    injection = check_prompt_injection(text)
    if not injection.passed:
        return injection
    return SecurityCheckResult(True)
