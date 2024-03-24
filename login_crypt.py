import json
import os
import sys
from base64 import b64decode, b64encode

from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto.Protocol.KDF import PBKDF2

SALT = b'5f92310b0d2ede28'
MASTER_PASSWORD = ''
KEY = b''


def init_crypto(master_password: str | None) -> bool:
    global MASTER_PASSWORD, KEY

    if master_password is None:
        return False

    backup_key = KEY
    MASTER_PASSWORD = master_password
    KEY = PBKDF2(MASTER_PASSWORD, SALT, 32, count=1_000_000, hmac_hash_module=SHA512)

    if decrypt_logins() is None:
        KEY = backup_key
        return False

    return True


def load_logins() -> dict:
    try:
        with open('logins.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        data = {}

    return data


def dump_logins(data: list | dict):
    with open('logins.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)


def encrypt_logins(logins: dict = None):
    if logins is None:
        logins = load_logins()

    nonce = os.urandom(16)
    cipher = AES.new(KEY, AES.MODE_EAX, nonce=nonce)

    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(logins).encode('utf-8'))

    enc_with_metadata = {'nonce': b64encode(nonce).decode(), 'tag': b64encode(tag).decode(),
                         'data': b64encode(ciphertext).decode()}
    dump_logins(enc_with_metadata)


def decrypt_logins():
    enc_logins = load_logins()

    if not enc_logins:
        return []

    nonce = b64decode(enc_logins['nonce'])
    cipher = AES.new(KEY, AES.MODE_EAX, nonce=nonce)

    try:
        logins = json.loads(cipher.decrypt_and_verify(b64decode(enc_logins['data']), b64decode(enc_logins['tag'])))
    except ValueError:
        print('Incorrect key')
        return None

    return logins
