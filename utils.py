import ctypes
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import firefox_connector

logging.basicConfig(level=logging.INFO)

TEMP_DIR = Path(tempfile.gettempdir()) / 'portable_password_manager'
PYTHON_DIR = Path(Path(__file__).parent.parent / 'python-embed')

assert (PYTHON_DIR.is_dir() and
        any([file.name.startswith('python') for file in PYTHON_DIR.glob('**/*')])), 'Python folder not found'


def init_local_windows():
    os.makedirs(TEMP_DIR, exist_ok=True)
    shutil.copy('firefox_connector.py', TEMP_DIR)
    shutil.copy('remove_passwords.py', TEMP_DIR)
    shutil.copy('utils.py', TEMP_DIR)

    subprocess.Popen(['robocopy', PYTHON_DIR, TEMP_DIR.parent / PYTHON_DIR.name, '/mt:64', '/e'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.Popen(['schtasks', '/delete', '/tn', 'PPM_USBEject', '/f'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    eventlog_check = subprocess.Popen(['wevtutil', 'gl', 'Microsoft-Windows-DriverFrameworks-UserMode/Operational'],
                                      stdout=subprocess.PIPE)

    if b'enabled: true' not in eventlog_check.stdout.read():
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', 'wevtutil',
                                            'sl Microsoft-Windows-DriverFrameworks-UserMode/Operational /e:true', None, 0)

    tree = ET.parse('windows_resources/PPM_USBEject_Base.xml')
    ET.register_namespace('', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
    root = tree.getroot()

    workdir_field = ET.Element('WorkingDirectory')
    workdir_field.text = str(TEMP_DIR.parent / PYTHON_DIR.name)
    root[4][0].insert(2, workdir_field)

    tree.write('PPM_USBEject.xml')

    task_creation = subprocess.Popen(['schtasks', '/create', '/tn', 'PPM_USBEject', '/xml', 'PPM_USBEject.xml'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    if task_creation.stderr.read():
        print('Failed to create task. Exiting...')
        sys.exit()

    logging.debug('Task successfully created.')


def init_local_linux():
    os.makedirs(TEMP_DIR, exist_ok=True)
    shutil.copy('firefox_connector.py', TEMP_DIR)
    shutil.copy('remove_passwords.py', TEMP_DIR)
    shutil.copy('utils.py', TEMP_DIR)

    subprocess.Popen(['cp', '-r', PYTHON_DIR, TEMP_DIR.parent])
    subprocess.Popen(f'env | grep HOME > {TEMP_DIR / ".env"}', shell=True)

    rule_init_command = fr'echo SUBSYSTEM==\"usb\", ACTION==\"remove\", ENV{{DEVTYPE}}==\"usb_device\", RUN=\"{TEMP_DIR / "remove_passwords.py"}\" > /etc/udev/rules.d/42-ppm-usb.rules'
    reload_rules_command = 'udevadm control --reload-rules'
    trigger_rule_command = 'udevadm trigger'
    reload_service_command = 'udevadm control --reload  '

    subprocess.Popen(
        f'pkexec bash -c \'{rule_init_command}; {reload_rules_command}; {trigger_rule_command}; {reload_service_command}\'',
        shell=True)


def check_url_match(valid_url: str, cand_url: str) -> bool:
    parsed_valid = urlparse(valid_url)
    parsed_cand = urlparse(cand_url)

    return parsed_valid.netloc in (parsed_cand.netloc, parsed_cand.path)


def insert_all_logins(current_logins: list[dict]):
    if not current_logins:
        print('Your DB is empty!')
        return

    try:
        with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as logins_file:
            added_logins = json.load(logins_file)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        added_logins = []

    all_logins = []

    for login in current_logins:
        all_logins.append((login['url'], login['login'], login['password']))

    added_logins += firefox_connector.add_logins(all_logins)

    with open(TEMP_DIR / 'added_logins.json', 'w', encoding='utf-8') as logins_file:
        json.dump(added_logins, logins_file)

    print('Success')


def insert_login(current_logins: list[dict], url: str):
    try:
        with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as logins_file:
            added_logins = json.load(logins_file)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        added_logins = []
    added_size = len(added_logins)

    for login in current_logins:
        if check_url_match(login['url'], url):
            added_logins += firefox_connector.add_logins([(login['url'], login['login'], login['password'])])

    with open(TEMP_DIR / 'added_logins.json', 'w', encoding='utf-8') as logins_file:
        json.dump(added_logins, logins_file)

    if len(added_logins) != added_size:
        print('Success')
    else:
        print('Login not found')
