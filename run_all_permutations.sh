#!/usr/bin/env fish

docker compose --project-directory .  -f generated/docker-compose.hollow.hostnet.http.yml down

PYTHONUNBUFFERED=1 ./run_all_permutations.py | tee ppp(date -u '+%Y-%m-%d-%H-%M-%S') | tee ppplast

