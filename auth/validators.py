import re


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,25}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.match(username.strip()))


def validate_password(password: str):
    errors = []

    if len(password) < 8:
        errors.append("Minimum 8 characters")

    if not re.search(r"[A-Z]", password):
        errors.append("At least 1 uppercase letter")

    if not re.search(r"[a-z]", password):
        errors.append("At least 1 lowercase letter")

    if not re.search(r"\d", password):
        errors.append("At least 1 number")

    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("At least 1 special character")

    return errors


def password_strength_level(password: str):
    checks = [
        len(password) >= 8,
        bool(re.search(r"[A-Z]", password)),
        bool(re.search(r"[a-z]", password)),
        bool(re.search(r"\d", password)),
        bool(re.search(r"[^A-Za-z0-9]", password)),
    ]

    score = sum(checks)

    if score <= 2:
        return "Weak", 0.33

    if score <= 4:
        return "Medium", 0.66

    return "Strong", 1.0