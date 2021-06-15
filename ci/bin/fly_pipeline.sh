#!/bin/bash

set -euo pipefail

: ${BRANCH}
: ${HTTPS_PROXY:="localhost:8118"}
: ${TARGET:=gcp}
: ${FLY:=fly -t ${TARGET}}
: ${EXTRA_OPTIONS:=""}


export HTTPS_PROXY=${HTTPS_PROXY}

WORKSPACE=`echo "${BRANCH:0:13}" | sed 's/[^a-zA-Z0-9]/-/g' | tr '[:upper:]' '[:lower:]'`
pipeline="baw-client-rest-${WORKSPACE}"


${FLY} set-pipeline \
    -p ${pipeline} \
    -c ci/pipeline.yml \
    -v "branch=${BRANCH}" \
    -v "workspace=${WORKSPACE}" \
    ${EXTRA_OPTIONS}


${FLY} unpause-pipeline \
    -p ${pipeline}