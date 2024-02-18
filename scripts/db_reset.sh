#! /bin/sh

# shellcheck disable=SC2046
cd $(dirname "$0")/.. || exit

poetry run python manage.py reset_db --noinput
poetry run python manage.py migrate
poetry run python manage.py devdata
poetry run python manage.py devdata_address_book
