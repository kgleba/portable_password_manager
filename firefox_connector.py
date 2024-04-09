import hmac
import json
import os
import sqlite3
import sys
from base64 import b64encode
from datetime import datetime
from hashlib import pbkdf2_hmac, sha1
from pathlib import Path
from uuid import uuid4

from Crypto.Cipher import AES, DES3
from Crypto.Util.Padding import pad
from dotenv import load_dotenv
from pyasn1.codec.der.decoder import Decoder, decode as der_decode
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1.type.univ import ObjectIdentifier, OctetString, Sequence

match sys.platform:
    case 'win32':
        PROFILE_DIR = Path(os.getenv('APPDATA')) / 'Mozilla/Firefox/Profiles'
    case 'linux':
        load_dotenv(Path(__file__).resolve().parent / '.env', override=True)
        PROFILE_DIR = Path(os.getenv('HOME', '')) / '.mozilla/firefox'
    case 'darwin':
        raise NotImplementedError('Module is not supported on Mac OS X yet')
    case _:
        raise EnvironmentError('Operating system is not recognized')

WORKDIR = None

for file in PROFILE_DIR.glob('**/*'):
    if file.name == 'key4.db':
        WORKDIR = file.parent
        break

if WORKDIR is None:
    print('Firefox profile folder not found, please specify it manually. Exiting...')
    sys.exit()

A102_CHECK = b'\xf8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
DES_SETUP = (1, 2, 840, 113_549, 3, 7)


def decrypt_AES(decoded_data: Decoder, master_password: str, global_salt: bytes):
    salt = decoded_data[0][0][1][0][1][0].asOctets()
    iteration_count = int(decoded_data[0][0][1][0][1][1])
    key_length = int(decoded_data[0][0][1][0][1][2])
    assert key_length == 32

    encoded_password = sha1(global_salt + master_password.encode('utf-8')).digest()
    encrypted_data = decoded_data[0][1].asOctets()

    key = pbkdf2_hmac('sha256', encoded_password, salt, iteration_count, dklen=key_length)
    iv = b'\x04\x0e' + decoded_data[0][0][1][1][1].asOctets()
    cipher = AES.new(key, AES.MODE_CBC, iv)

    return cipher.decrypt(encrypted_data)


def decrypt_3DES(global_salt: bytes, master_password: str, salt: bytes, encrypted_data: bytes):
    hashed_password = sha1(global_salt + master_password.encode('utf-8')).digest()
    padded_salt = salt.ljust(20, b'\x00')
    salted_password = sha1(hashed_password + salt).digest()

    key_component1 = hmac.new(salted_password, padded_salt + salt, sha1).digest()
    temp_key = hmac.new(salted_password, padded_salt, sha1).digest()
    key_component2 = hmac.new(salted_password, temp_key + salt, sha1).digest()

    param_source = key_component1 + key_component2
    iv = param_source[-8:]
    key = param_source[:24]
    cipher = DES3.new(key, DES3.MODE_CBC, iv)

    return cipher.decrypt(encrypted_data)


def get_key(master_password: str = ''):
    db_file = WORKDIR / 'key4.db'

    with sqlite3.connect(db_file) as connection:
        cursor = connection.cursor()

        cursor.execute('''
        SELECT item1, item2
        FROM metadata
        WHERE id = 'password';
        ''')

        try:
            global_salt, data = next(cursor)
            decoded_data, _ = der_decode(data)
            encryption_method = '3DES'

            salt = decoded_data[0][1][0].asOctets()
            ciphertext = decoded_data[1].asOctets()
            plaintext = decrypt_3DES(global_salt, master_password, salt, ciphertext)
        except AttributeError:
            encryption_method = 'AES'
            decoded_data = der_decode(data)
            plaintext = decrypt_AES(decoded_data, master_password, global_salt)
        except StopIteration:
            print('Firefox key not found. Please add entry to your browser manually. Exiting...')
            sys.exit()

        assert plaintext == pad(b'password-check', 16)

        cursor.execute('''
        SELECT a11, a102
        FROM nssPrivate
        WHERE a102 = ?;
        ''', (A102_CHECK,))

        a11, _ = next(cursor)  # CKA_ID

        if encryption_method == '3DES':
            decoded_a11, _ = der_decode(a11)
            salt = decoded_a11[0][1][0].asOctets()
            ciphertext = decoded_a11[1].asOctets()
            key = decrypt_3DES(global_salt, master_password, salt, ciphertext)
        elif encryption_method == 'AES':
            decoded_a11 = der_decode(a11)
            key = decrypt_AES(decoded_a11, master_password, global_salt)

    return key[:24]


def encode_data(key: bytes, data: str):
    iv = os.urandom(8)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(data.encode('utf-8'), 8))

    asn1_data = Sequence()
    asn1_data[0] = OctetString(A102_CHECK)
    asn1_data[1] = Sequence()
    asn1_data[1][0] = ObjectIdentifier(DES_SETUP)
    asn1_data[1][1] = OctetString(iv)
    asn1_data[2] = OctetString(ciphertext)

    return b64encode(der_encode(asn1_data)).decode()


def load_logins() -> dict:
    try:
        with open(WORKDIR / 'logins.json', 'r', encoding='utf-8') as logins_file:
            data = json.load(logins_file)
    except json.decoder.JSONDecodeError:
        data = {'nextId': 1, 'logins': []}

    return data


def dump_logins(data: dict):
    with open(WORKDIR / 'logins.json', 'w', encoding='utf-8') as logins_file:
        json.dump(data, logins_file, ensure_ascii=False, separators=(',', ':'))


def add_logins(upd_logins: list[tuple]) -> range:
    logins = load_logins()

    next_id = logins['nextId']
    timestamp = int(datetime.now().timestamp() * 1000)

    for i, (url, username, password) in enumerate(upd_logins, start=next_id):
        entry = {
            'id': i,
            'hostname': url,
            'httpRealm': None,
            'formSubmitURL': '',
            'usernameField': '',
            'passwordField': '',
            'encryptedUsername': encode_data(KEY, username),
            'encryptedPassword': encode_data(KEY, password),
            'guid': f'{{{uuid4()}}}',
            'encType': 1,
            'timeCreated': timestamp,
            'timeLastUsed': timestamp,
            'timePasswordChanged': timestamp,
            'timesUsed': 0,
        }
        logins['logins'].append(entry)

    logins['nextId'] += len(upd_logins)

    dump_logins(logins)

    return range(next_id, logins['nextId'])


def remove_logins_by_id(upd_logins: list[int]):
    logins = load_logins()

    cleaned_logins = []
    current_id = 1

    for login in logins['logins']:
        for login_id in upd_logins:
            if login_id == login['id']:
                break
        else:
            login['id'] = current_id
            cleaned_logins.append(login)
            current_id += 1

    logins_modifier = {'nextId': current_id, 'logins': cleaned_logins}

    dump_logins(logins | logins_modifier)


KEY = get_key()
