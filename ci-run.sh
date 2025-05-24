#!/bin/bash
set -euo pipefail

# Script to run the stack in CI mode
# Generates customized docker-compose files based on parameters

# Parse arguments
HOLLOW=${1:-false}
HOST_NETWORK=${2:-false}
HTTP=${3:-true}
RUN_TESTS=${4:-true}
GENERATE=${5:-true}

if [ "$GENERATE" = "true" ]; then
  # Generate the customized docker-compose file with Dockerfiles
  echo "Generating Dockerfiles and compose file..."
  scripts/generate_compose.py --hollow=$HOLLOW --host-network=$HOST_NETWORK --http=$HTTP
fi


export HOLLOW
export HOST_NETWORK
export HTTP
INSTANTIATION=`./instantiation.sh`
# The generated compose file
COMPOSE_FILE="generated/docker-compose.${INSTANTIATION}.yml"
echo "Using compose file: $COMPOSE_FILE"

# Set environment variables
export CI=true
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
echo "Running with USER_ID=$USER_ID and GROUP_ID=$GROUP_ID"

# Create necessary directories for Playwright
echo "Creating test result directories..."
mkdir -p test-results playwright-report

if [ "$HTTP" = "false" ]; then
  # create a self-signed certificate if it doesn't exist
  if [ ! -f certs/server.crt ]; then
    echo "Generating self-signed certificate..."
    ./mkcerts.sh
  fi
  echo "Running with HTTPS enabled"
else
  echo "Running with HTTPS disabled"
fi

if [ "$RUN_TESTS" = "true" ]; then
  # Start services, run tests, then shut down
  set -x
  
  docker compose --project-directory . -f $COMPOSE_FILE up --build --detach --remove-orphans

  # Run tests with the Playwright container
  echo "Running tests with Playwright container..."
  docker compose --project-directory . -f $COMPOSE_FILE run playwright
  TEST_EXIT_CODE=$?

  # Collect logs and shut down
  echo "Collecting logs and shutting down..."
  docker compose --project-directory . -f $COMPOSE_FILE logs > docker-compose.log
  docker compose --project-directory . -f $COMPOSE_FILE down
  
  # Exit with the test exit code
  exit $TEST_EXIT_CODE
else
  # Just run everything and keep it running
  echo "Running services without tests..."
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE up --build --remove-orphans
fi
