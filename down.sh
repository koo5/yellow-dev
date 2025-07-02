#!/bin/bash
set -x
docker compose --project-directory . -f ./generated/last.yml down

