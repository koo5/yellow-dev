#!/usr/bin/env sh

USER_ID=$(id -u) GROUP_ID=$(id -g) docker compose -f docker-compose.yml up --build --remove-orphans