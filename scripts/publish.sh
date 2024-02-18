#! /bin/sh

# shellcheck disable=SC2046
cd $(dirname "$0")/.. || exit

poe check && \
poetry build && \
poetry publish
