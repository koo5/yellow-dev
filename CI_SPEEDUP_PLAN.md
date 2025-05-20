# CI Speedup Plan

=============

0. in scripts/run_compose_and_test.py, introduce "hollow" argument, defaulting to False. Introduce HOLLOW env var.
=============



1. introduce "full" and "hollow" mode. The idea is that in hollow mode, containers only get bind-mounted app sources dir, and their startup scripts install packages. In "full" mode, the hollow base images are first built, and then they are used as bases for "full" images that first COPY package lock files and install packages, then copy app sources, so that no bind-mount from outside is necessary:
this is what chatgpt has to say about having docker compose first build base images and then build containers with different images that build off the base images:


1. Two separate builds + an explicit tag

# docker-compose.yml
services:

  base:
    build:
      context: ./docker/base
      dockerfile: Dockerfile
    image: myorg/my-base:latest

  app:
    build:
      context: ./docker/app
      dockerfile: Dockerfile
      # <-- no special “dependency” field here
    image: myorg/my-app:latest

    Base image
    In ./docker/base/Dockerfile you build out your “base” layers (apt installs, language runtimes, etc).

    App image
    In ./docker/app/Dockerfile you simply start with:

    FROM myorg/my-base:latest
    COPY . .
    RUN make / build / whatever

If you run:

docker-compose build

Compose will execute both builds in the order they appear in the file (older Compose versions build sequentially; if you’re on a newer CLI that defaults to parallel you can force sequential with --no-parallel or by explicitly building docker-compose build base app). As long as the base image is built (and tagged) first, the second build will pick it up locally rather than pulling from Docker Hub.
2. Multi-stage Dockerfile + build targets

If you’d rather keep everything in one Git repo and one Dockerfile, take advantage of Docker’s multi-stage builds:

# ./docker/app/Dockerfile

# ─── stage 1: base ───
FROM ubuntu:24.04 AS base
RUN apt update && apt install -y python3 python3-pip …  

# ─── stage 2: build ───
FROM base AS builder
WORKDIR /src
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# ─── stage 3: final ───
FROM base
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . /app
CMD ["python3","main.py"]

Then in your Compose file:

services:
  app:
    build:
      context: ./docker/app
      dockerfile: Dockerfile
      # you could explicitly build only the “builder” stage if you wanted:
      # target: builder
    image: myorg/my-app:latest

    Intermediate caching: Docker caches each stage by name (base, builder, etc), so any future build that references FROM base will reuse those layers from the cache even if it’s a different service in the same Compose file.




===============




in full mode, walk through all services and remove their volume sections. Output a modified docker-compose file

===============

## Playwright Container

1. Create dedicated Playwright container:
   - Create a new Dockerfile for running Playwright tests
   - Include both client and admin code in the container
   - Pre-install all testing dependencies
   - Configure for headless browser testing

2. Update the test running script:
   - Launch the Playwright container instead of running tests directly
   - Pass test results back to the CI environment
   - Configure proper networking with other containers

==============================



## Caching and BuildX Configuration

1. Reintroduce BuildX caching:
   - Configure GitHub Actions to use BuildX
   - Set up proper caching between workflow runs

