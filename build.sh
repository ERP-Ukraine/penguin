#!/bin/sh

VERSION="v5.8"
docker build -t erpukraine/custom:penguin-13.0-${VERSION} . && \
docker push erpukraine/custom:penguin-13.0-${VERSION}
# sed -i 's/penguin-13.0-...../penguin-13.0-'${VERSION}'/' ./docker-compose.yml
