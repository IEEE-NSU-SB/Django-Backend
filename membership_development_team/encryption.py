
from insb_port import settings
from cryptography.fernet import Fernet

def get_fernet():
    return Fernet(settings.ENCRYPTION_KEY)

def encrypt_string(plain_text):
    f = get_fernet()
    return f.encrypt(plain_text.encode()).decode()

def decrypt_string(encrypted_text):
    f = get_fernet()
    return f.decrypt(encrypted_text.encode()).decode()