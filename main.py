from __future__ import print_function, unicode_literals

import sys
from pathlib import Path

import validators
from PyInquirer import print_json, prompt
from prompt_toolkit.validation import ValidationError, Validator

import utils
from login_crypt import decrypt_logins, dump_logins, encrypt_logins, init_crypto

INITIALIZED_LOCAL = False

DB_PATH = Path('logins.json')


class URLValidator(Validator):
    def validate(self, document):
        if not validators.url(document.text):
            raise ValidationError(
                message='Enter valid URL',
                cursor_position=len(document.text))


class EmptinessValidator(Validator):
    def validate(self, document):
        if not document.text:
            raise ValidationError(
                message='Field could not be empty',
                cursor_position=len(document.text))


auth_selector = [
    {
        'type': 'password',
        'name': 'master_password',
        'message': 'Enter Master Password for the encrypted data:'
    }
]

action_selector = [
    {
        'type': 'list',
        'name': 'action',
        'message': 'Select action you want to perform:',
        'choices': ['Insert entry to browser', 'Add entry to DB', 'Remove entry from DB',
                    'Show DB entries (without passwords)', 'Show full DB entries (requires authorization)',
                    'Exit']
    }
]

add_parameter_selectors = [
    {
        'type': 'input',
        'name': 'url',
        'message': 'Enter URL of the entry:',
        'validate': URLValidator
    },
    {
        'type': 'input',
        'name': 'login',
        'message': 'Enter login of the entry:',
        'filter': lambda val: val.strip(),
        'validate': EmptinessValidator
    },
    {
        'type': 'password',
        'name': 'password',
        'message': 'Enter password of the entry:',
        'filter': lambda val: val.strip(),
        'validate': EmptinessValidator
    }
]

remove_parameter_selectors = [
    {
        'type': 'input',
        'name': 'url',
        'message': 'Enter URL of the entry:',
        'validate': URLValidator
    },
    {
        'type': 'input',
        'name': 'login',
        'message': 'Enter login of the entry (leave blank if you don\'t want to include it in query):',
        'filter': lambda val: val.strip()
    },
    {
        'type': 'password',
        'name': 'password',
        'message': 'Enter password of the entry (leave blank if you don\'t want to include it in query):',
        'filter': lambda val: val.strip()
    }
]

insert_parameter_selectors = [
    {
        'type': 'confirm',
        'name': 'insert_all',
        'message': 'Do you want to insert all stored entries?',
        'default': False
    },
    {
        'type': 'input',
        'name': 'url',
        'message': 'Enter URL of the entry:',
        'validate': URLValidator,
        'when': lambda answers: not answers['insert_all']
    }
]

if DB_PATH.is_file():
    master_password = prompt.prompt(auth_selector)['master_password']
    if not init_crypto(master_password):
        sys.exit()
else:
    print('Master Password for the DB is not set (proceed only in safe environment!)')
    initial_password = prompt.prompt(auth_selector)['master_password']
    init_crypto(initial_password)

    dump_logins([])
    encrypt_logins()

while True:
    action = prompt.prompt(action_selector)['action']
    current_logins = decrypt_logins()

    match action:
        case 'Exit':
            break
        case 'Insert entry to browser':
            parameters = prompt.prompt(insert_parameter_selectors)

            if not INITIALIZED_LOCAL:
                if not utils.init_local():
                    sys.exit()
                INITIALIZED_LOCAL = True

            if parameters.get('insert_all'):
                utils.insert_all_logins(current_logins)
            else:
                utils.insert_login(current_logins, parameters.get('url'))
        case 'Add entry to DB':
            parameters = prompt.prompt(add_parameter_selectors)
            url, login, password = parameters.values()

            formed_login = {'url': url, 'login': login, 'password': password}
            current_logins.append(formed_login)
            encrypt_logins(current_logins)
        case 'Remove entry from DB':
            parameters = prompt.prompt(remove_parameter_selectors)
            url, login, password = parameters.values()

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
                print('No entries found')
                continue
            if found_entries > 1:
                print('More than one entry found')
                continue

            current_logins.remove(found_entry)
            encrypt_logins(current_logins)
        case 'Show DB entries (without passwords)':
            for login in current_logins:
                login['password'] = '*' * 10

            for login in current_logins:
                print_json(login)
        case 'Show full DB entries (requires authorization)':
            master_password = prompt.prompt(auth_selector)['master_password']
            if not init_crypto(master_password):
                sys.exit()

            for login in current_logins:
                print_json(login)

    del current_logins
