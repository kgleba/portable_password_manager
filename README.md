# Portable Password Manager

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/kgleba/portable_password_manager/blob/main/README.md)
[![ru](https://img.shields.io/badge/lang-ru-green.svg)](https://github.com/kgleba/portable_password_manager/blob/main/README.ru.md)

## Installation

Download the [latest release](https://github.com/kgleba/portable_password_manager/releases/latest) with the desired OS, unzip it, and copy the files to your flash drive. Your password manager is ready to go!

Or, if you want to create a development build:

1) Install Docker on your host machine
2) Fork this repository and commit changes 
3) Create folder `packages` and run the Docker container (note that you can adjust the `PYTHON_VERSION` and `PACKAGE_VERSION` variables):
```shell
mkdir packages

# for Windows build
docker build -t ppm_packager_windows --file .\windows_resources\Dockerfile --build-arg PACKAGE_VERSION=latest .
docker run --mount type=bind,source=.\packages,destination=/dist ppm_packager_windows

# for Linux build
docker build -t ppm_packager_linux --file .\linux_resources\Dockerfile --build-arg PACKAGE_VERSION=latest .
docker run --mount type=bind,source=.\packages,destination=/dist ppm_packager_linux
```
4) Unzip the build to your flash drive. Your password manager is ready to go!

## Firefox

<u>NB</u> Make sure that you have at least once inserted a password into your browser manually. Otherwise, soft won't be
able to retrieve and store your passwords.

If you want to reset the password for the DB, enter incorrect passwords 3 times or simply delete `logins.json` from a project directory

Note that resetting the password for the DB will wipe out all stored entries!

It's important that you relaunch your Firefox instance after each insertion. Otherwise, Firefox won't see the changes
that were made. I'm working on that inconvenience.

## Usage

On Windows (not that convenient yet):

```shell
cd portable_password_manager
..\python-embed\python main.py
```

On Linux:

```shell
cd portable_password_manager
./main.py
```

... and follow the text interface instructions!

## TODO

* Include a function that updates Firefox password storage in the runtime
* Implement support for Mozilla Firefox internal storage master password
* Add flash drive specification for the USB ejection task 
* Check `installs.ini` and `profiles.ini` in Mozilla folder
* Implement Google Chrome support
