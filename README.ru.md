# Portable Password Manager

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/kgleba/portable_password_manager/blob/main/README.md)
[![ru](https://img.shields.io/badge/lang-ru-green.svg)](https://github.com/kgleba/portable_password_manager/blob/main/README.ru.md)

## Установка

Загрузите [последний выпуск](https://github.com/kgleba/portable_password_manager/releases/latest) для желаемой ОС, распакуйте его, и скопируйте файлы на флеш-накопитель. Ваш менеджер паролей готов к использованию!

Или, если вы хотите создать сборку для разработки:

1) Установите Docker на вашу хост-машину
2) Создайте форк данного репозитория и внесите желаемые изменения
3) Создайте папку `packages` и запустите Docker-контейнер (обратите внимание, что вы можете менять параметры `PYTHON_VERSION` и `PACKAGE_VERSION`):
```shell
mkdir packages

# для сборки под Windows
docker build -t ppm_packager_windows --file .\windows_resources\Dockerfile --build-arg PACKAGE_VERSION=latest .
docker run --mount type=bind,source=.\packages,destination=/dist ppm_packager_windows

# для сборки под Linux
docker build -t ppm_packager_linux --file .\linux_resources\Dockerfile --build-arg PACKAGE_VERSION=latest .
docker run --mount type=bind,source=.\packages,destination=/dist ppm_packager_linux
```
4) Распакуйте сборку на флеш-накопитель. Ваш менеджер паролей готов к использованию!

## Firefox

<u>NB</u> Убедитесь, что вы хотя бы раз вводили пароль в браузер вручную. В противном случае решение не сможет обнаружить и сохранить ваши пароли.

Если вы хотите сбросить пароль от базы данных, трижды введите произвольный пароль при запросе или просто удалите `logins.json` из папки проекта.

Обратите внимание, что сброс пароля от БД приведет к удалению всех сохраненных записей!

Важно, чтобы вы перезапускали экземпляр Firefox после каждого добавления записей. В противном случае Firefox не увидит изменений, которые были сделаны.

## Использование

На ОС Windows:

```shell
cd portable_password_manager
..\python-embed\python main.py
```

На ОС Linux:

```shell
cd portable_password_manager
./main.py
```

... и следуйте указаниям текстового интерфейса!
