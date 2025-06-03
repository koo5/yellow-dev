#!/bin/bash
set -euo pipefail

sudo apt update; sudo apt install -y docker.io docker-compose-v2 python3-yaml
./ci-run.sh true true true false false
