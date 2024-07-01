#!/bin/sh

VERSION="v8.6"
docker build -t erpukraine/custom:penguin-17.0-${VERSION} . && \
docker push erpukraine/custom:penguin-17.0-${VERSION}
# sed -i 's/penguin-17.0-...../penguin-17.0-'${VERSION}'/' ./docker-compose.yml
