FROM debian:bookworm-slim

ARG PYTHON_VERSION=3.11.8
ARG PACKAGE_VERSION=latest
ENV PACKAGE_VERSION=${PACKAGE_VERSION}

RUN apt update && apt install -y wget git zip

WORKDIR /build

# don't forget to synchronize the release tag and the desired CPython version
# 20240224 is limited to [3.8.18, 3.9.18, 3.10.13, 3.11.8, 3.12.2]
RUN wget -qO- https://github.com/indygreg/python-build-standalone/releases/download/20240224/cpython-${PYTHON_VERSION}+20240224-x86_64-unknown-linux-gnu-install_only.tar.gz | tar -xz && mv python python-embed

RUN git clone https://github.com/kgleba/portable_password_manager
RUN ./python-embed/bin/pip install -r portable_password_manager/requirements.txt && ./python-embed/bin/pip install pycryptodome

WORKDIR portable_password_manager
RUN printf '#!/bin/sh\n"exec" "$(dirname $0)/../python-embed/bin/python" "$0" "$@"\n\n' | cat - main.py > tempfile && mv tempfile main.py
RUN printf '#!/bin/sh\n"exec" "$(dirname $0)/../python-embed/bin/python" "$0" "$@"\n\n' | cat - remove_passwords.py > tempfile && mv tempfile remove_passwords.py
RUN chmod +x main.py && chmod +x remove_passwords.py

WORKDIR /build
ENTRYPOINT zip -r -q /dist/ppm_package_linux_${PACKAGE_VERSION}.zip .