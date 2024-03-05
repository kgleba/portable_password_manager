import json
import os
import shutil
import subprocess
from pathlib import Path

import firefox_connector

TEMP_DIR = Path(os.getenv('TEMP')) / 'portable_password_manager'

try:
    with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as file:
        added_logins = json.load(file)
except (json.decoder.JSONDecodeError, FileNotFoundError):
    added_logins = []

firefox_connector.remove_logins_by_domain(added_logins)

subprocess.Popen(['schtasks', '/delete', '/tn', 'PPM_USBEject', '/f'])

try:
    shutil.rmtree(TEMP_DIR)
except PermissionError:
    pass
