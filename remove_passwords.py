import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import firefox_connector

TEMP_DIR = Path(tempfile.gettempdir()) / 'portable_password_manager'

try:
    with open(TEMP_DIR / 'added_logins.json', 'r', encoding='utf-8') as file:
        added_logins = json.load(file)
except (json.decoder.JSONDecodeError, FileNotFoundError):
    added_logins = []

firefox_connector.remove_logins_by_id(added_logins)

match sys.platform:
    case 'win32':
        subprocess.Popen(['schtasks', '/delete', '/tn', 'PPM_USBEject', '/f'])
    case 'linux':
        subprocess.Popen(['rm', '/etc/udev/rules.d/42-ppm-usb.rules'])

shutil.rmtree(TEMP_DIR, ignore_errors=True)
