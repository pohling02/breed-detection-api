import secrets
import string

def generate_secure_api_key(prefix="sk_"):
    # Generates a 32-character random string of letters and numbers
    alphabet = string.ascii_letters + string.digits
    secure_string = "".join(secrets.choice(alphabet) for _ in range(32))
    return f"{prefix}{secure_string}"