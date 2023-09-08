import hashlib
import os


class Util:
    def generate_salt():
        return os.urandom(16)

    def generate_hash(password, salt):
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            dklen=16
        )
        return key
