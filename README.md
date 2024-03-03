# Portable Password Manager

The project is in development right now :)

## Installation (on Windows)

```shell
git clone https://github.com/kgleba/portable_password_manager
cd portable_password_manager
python -m venv venv
./venv/Scripts/activate.bat
pip install -r requirements.txt
```

## Firefox

<u>NB</u> Make sure that you have at least once inserted a password into your browser manually. Otherwise, soft won't be able to retrieve and store your passwords.

If you want to reset the password for the DB, simply delete `logins.json` from a project directory and run `main.py`

Note that resetting the password for the DB will wipe out all stored entries!

## Usage

```shell
python main.py
```
... and follow the text interface instructions!

## TODO

* Create and test release with a packaged Python environment
* Implement Google Chrome support
* Implement Linux support