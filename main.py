from __future__ import print_function, unicode_literals

import gettext
import os
import sys
import warnings
from pathlib import Path
from typing import Callable

import validators
from PyInquirer import print_json, prompt
from prompt_toolkit.validation import ValidationError, Validator

import locale
import utils
from login_crypt import decrypt_logins, dump_logins, encrypt_logins, init_crypto

warnings.filterwarnings('ignore', category=DeprecationWarning)

DB_PATH = Path('logins.json')

if sys.platform == 'win32':
    os.system('color')


def get_translation(lang: str) -> Callable:
    translation = gettext.translation('ppm', 'locale', (lang,))
    return translation.gettext


_ = get_translation(locale.getdefaultlocale()[0])


class URLValidator(Validator):
    def validate(self, document):
        if not validators.url(document.text):
            raise ValidationError(
                message=_('Enter valid URL'),
                cursor_position=len(document.text))


class EmptinessValidator(Validator):
    def validate(self, document):
        if not document.text:
            raise ValidationError(
                message=_('Field could not be empty'),
                cursor_position=len(document.text))


class Selector:
    @classmethod
    @property
    def auth(cls):
        return [
            {
                'type': 'password',
                'name': 'master_password',
                'message': _('Enter Master Password for the encrypted data:'),
                'validate': EmptinessValidator
            }
        ]

    @classmethod
    @property
    def reset(cls):
        return [
            {
                'type': 'confirm',
                'name': 'reset_password',
                'message': _('Do you want to reset DB password?'),
                'default': False
            }
        ]

    @classmethod
    @property
    def action(cls):
        return [
            {
                'type': 'list',
                'name': 'action',
                'message': _('Select action you want to perform:'),
                'choices': [
                    {
                        'name': _(choice),
                        'value': choice
                    }
                    for choice in
                    ('Insert entry to browser', 'Add entry to DB', 'Remove entry from DB',
                     'Show DB entries (without passwords)',
                     'Show full DB entries (requires authorization)', 'Change application language', 'Exit')
                ]
            }
        ]

    @classmethod
    @property
    def add_parameters(cls):
        return [
            {
                'type': 'input',
                'name': 'url',
                'message': _('Enter URL of the entry:'),
                'validate': URLValidator
            },
            {
                'type': 'input',
                'name': 'login',
                'message': _('Enter login of the entry:'),
                'filter': lambda val: val.strip(),
                'validate': EmptinessValidator
            },
            {
                'type': 'password',
                'name': 'password',
                'message': _('Enter password of the entry:'),
                'filter': lambda val: val.strip(),
                'validate': EmptinessValidator
            }
        ]

    @classmethod
    @property
    def remove_parameters(cls):
        return [
            {
                'type': 'input',
                'name': 'url',
                'message': _('Enter URL of the entry:'),
                'validate': URLValidator
            },
            {
                'type': 'input',
                'name': 'login',
                'message': _('Enter login of the entry (leave blank if you don\'t want to include it in query):'),
                'filter': lambda val: val.strip()
            },
            {
                'type': 'password',
                'name': 'password',
                'message': _('Enter password of the entry (leave blank if you don\'t want to include it in query):'),
                'filter': lambda val: val.strip()
            }
        ]

    @classmethod
    @property
    def insert_parameters(cls):
        return [
            {
                'type': 'confirm',
                'name': 'insert_all',
                'message': _('Do you want to insert all stored entries?'),
                'default': False
            },
            {
                'type': 'input',
                'name': 'url',
                'message': _('Enter URL of the entry:'),
                'validate': URLValidator,
                'when': lambda answers: not answers['insert_all']
            }
        ]

    @classmethod
    @property
    def language(cls):
        return [
            {
                'type': 'list',
                'name': 'language',
                'message': _('Choose the preferred locale (language):'),
                'choices': [ll.name for ll in Path('locale').iterdir() if ll.is_dir()]
            }
        ]


match sys.platform:
    case 'win32':
        utils.init_local_windows()
    case 'linux':
        utils.init_local_linux()


def set_password():
    print(_('Master Password for the DB is not set (proceed only in safe environment!)'))
    initial_password = prompt.prompt(Selector.auth).get('master_password')
    init_crypto(initial_password)

    dump_logins([])
    encrypt_logins()


if DB_PATH.is_file():
    for i in range(3):
        master_password = prompt.prompt(Selector.auth).get('master_password')
        if init_crypto(master_password):
            break
    else:
        reset_password = prompt.prompt(Selector.reset).get('reset_password')
        if reset_password:
            DB_PATH.unlink(missing_ok=True)
            set_password()
        else:
            sys.exit()
else:
    set_password()

while True:
    action = prompt.prompt(Selector.action).get('action')
    current_logins = decrypt_logins()

    match action:
        case 'Exit':
            break
        case 'Insert entry to browser':
            parameters = prompt.prompt(Selector.insert_parameters)

            if parameters.get('insert_all'):
                utils.insert_all_logins(current_logins)
            else:
                utils.insert_login(current_logins, parameters.get('url'))
        case 'Add entry to DB':
            parameters = prompt.prompt(Selector.add_parameters)
            try:
                url, login, password = parameters.values()
            except ValueError:
                continue

            formed_login = {'url': url, 'login': login, 'password': password}
            current_logins.append(formed_login)
            encrypt_logins(current_logins)
        case 'Remove entry from DB':
            parameters = prompt.prompt(Selector.remove_parameters)
            try:
                url, login, password = parameters.values()
            except ValueError:
                continue

            found_entries = 0
            found_entry = None

            for entry in current_logins:
                if not utils.check_url_match(entry['url'], url):
                    continue
                if login and entry['login'] != login:
                    continue
                if password and entry['password'] != password:
                    continue

                found_entries += 1
                found_entry = entry

            if found_entries == 0:
                print(_('No entries found'))
                continue
            if found_entries > 1:
                print(_('More than one entry found'))
                continue

            current_logins.remove(found_entry)
            encrypt_logins(current_logins)
        case 'Show DB entries (without passwords)':
            for login in current_logins:
                login['password'] = '*' * 10

            for login in current_logins:
                print_json(login)
        case 'Show full DB entries (requires authorization)':
            master_password = prompt.prompt(Selector.auth).get('master_password')
            if not init_crypto(master_password):
                continue

            for login in decrypt_logins():
                print_json(login)
        case 'Change application language':
            language = prompt.prompt(Selector.language).get('language')

            _ = get_translation(language)

    del current_logins
