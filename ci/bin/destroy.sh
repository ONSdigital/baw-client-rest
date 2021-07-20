#!/bin/bash

set -euo pipefail

: ${HTTPS_PROXY:="localhost:8118"}
: ${TARGET:=gcp}
: ${FLY:=fly -t ${TARGET}}
: ${EXTRA_OPTIONS:=""}


export HTTPS_PROXY=${HTTPS_PROXY}

pipeline="baw-client-rest"

${FLY} destroy-pipeline -p ${pipeline} --non-interactive
