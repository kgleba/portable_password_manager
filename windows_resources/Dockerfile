ARG PYTHON_VERSION=3.11.8

FROM python:${PYTHON_VERSION}-slim-bookworm

ARG PACKAGE_VERSION=latest
ENV PACKAGE_VERSION=${PACKAGE_VERSION}

RUN apt update && apt install -y wget git zip busybox gettext

WORKDIR /build

ADD windows_resources/pycryptodome-3.20.0-cp35-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl .

RUN wget -qO- https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip | busybox unzip -d python-embed -

RUN git clone https://github.com/kgleba/portable_password_manager
RUN cd python-embed && mkdir site-packages && pip install -r ../portable_password_manager/requirements.txt -t ./site-packages
RUN cd python-embed && PTH_FILE=$(find . -regex '.*\._pth') && printf 'site-packages\n../portable_password_manager\n' | cat - $PTH_FILE > tempfile && mv tempfile $PTH_FILE
RUN pip install pycryptodome-3.20.0-cp35-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl -t ./python-embed/site-packages && rm pycryptodome-3.20.0-cp35-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl

RUN cd portable_password_manager/locale/en_US/LC_MESSAGES && msgfmt -o ppm.mo ppm.po
RUN cd portable_password_manager/locale/ru_RU/LC_MESSAGES && msgfmt -o ppm.mo ppm.po

ENTRYPOINT zip -r -q /dist/ppm_package_windows_${PACKAGE_VERSION}.zip .