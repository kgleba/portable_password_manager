import json
import logging
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import firefox_connector

logging.basicConfig(level=logging.INFO)

TEMP_DIR = Path(os.getenv('TEMP')) / 'portable_password_manager'


def init_local() -> bool:
    os.makedirs(TEMP_DIR, exist_ok=True)
    shutil.copy('firefox_connector.py', TEMP_DIR)
    shutil.copy('remove_passwords.py', TEMP_DIR)
    shutil.copy('utils.py', TEMP_DIR)

    subprocess.Popen(['schtasks', '/delete', '/tn', 'PPM_USBEject', '/f'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    tree = ET.parse('PPM_USBEject_Base.xml')
    ET.register_namespace('', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
    root = tree.getroot()

    workdir_field = ET.Element('WorkingDirectory')
    workdir_field.text = str(TEMP_DIR)
    root[4][0].insert(2, workdir_field)

    tree.write('PPM_USBEject.xml')

    task_creation = subprocess.Popen(['schtasks', '/create', '/tn', 'PPM_USBEject', '/xml', 'PPM_USBEject.xml'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    if task_creation.stderr.read():
        print('Failed to create task. Exiting...')
        return False

    logging.debug('Task successfully created.')

    return True


def check_url_match(valid_url: str, cand_url: str) -> bool:
    parsed_valid = urlparse(valid_url)
    parsed_cand = urlparse(cand_url)

    return parsed_valid.netloc in (parsed_cand.netloc, parsed_cand.path)


def insert_all_logins(current_logins: list[dict]):
    try:
        with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as file:
            added_logins = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        added_logins = []
    added_size = len(added_logins)

    all_logins = []

    for login in current_logins:
        all_logins.append((login['url'], login['login'], login['password']))
        added_logins.append(login['url'])

    firefox_connector.add_logins(all_logins)

    with open(TEMP_DIR / 'added_logins.json', 'w', encoding='utf-8') as file:
        json.dump(added_logins, file)

    if len(added_logins) != added_size:
        print('Success')
    else:
        print('Login not found')


def insert_login(current_logins: list[dict], url: str):
    try:
        with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as file:
            added_logins = json.load(file)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        added_logins = []
    added_size = len(added_logins)

    for login in current_logins:
        if check_url_match(login['url'], url):
            firefox_connector.add_logins([(login['url'], login['login'], login['password'])])
            added_logins.append(login['url'])

    with open(TEMP_DIR / 'added_logins.json', 'w', encoding='utf-8') as file:
        json.dump(added_logins, file)

    if len(added_logins) != added_size:
        print('Success')
    else:
        print('Login not found')
