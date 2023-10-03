#!/bin/bash

set -e

RASA_VERSION=${RASA_VERSION:-3.2.5}

docker build \
    --target conda \
    -t "pkeller/rasa-aarch64:conda-${RASA_VERSION}" \
    --build-arg RASA_VERSION=${RASA_VERSION} \
    .

docker build \
    -t "pkeller/rasa-aarch64:${RASA_VERSION}" \
    -t "pkeller/rasa-aarch64:latest" \
    --build-arg RASA_VERSION=${RASA_VERSION} \
    .
