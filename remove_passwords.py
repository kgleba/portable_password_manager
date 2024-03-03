import json
import os
import shutil
import subprocess
from pathlib import Path

import firefox_connector

TEMP_DIR = Path(os.getenv('TEMP')) / 'portable_password_manager'

with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as file:
    added_logins = json.load(file)

firefox_connector.remove_logins_by_domain(added_logins)

subprocess.Popen(['schtasks', '/delete', '/tn', 'PPM_USBEject', '/f'])

try:
    shutil.rmtree('.')
except PermissionError:
    pass
