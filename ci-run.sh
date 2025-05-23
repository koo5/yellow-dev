#!/bin/bash
set -euo pipefail

# Script to run the stack in CI mode
# Generates customized docker-compose files based on parameters

# Parse arguments
HOLLOW=${1:-false}
HOST_NETWORK=${2:-false}
HTTPS=${3:-false}
RUN_TESTS=${3:-true}
GENERATE=${4:-false}

if [ "$GENERATE" = "true" ]; then
  # Generate the customized docker-compose file with Dockerfiles
  echo "Generating Dockerfiles and compose file..."
  scripts/generate_compose.py --hollow=$HOLLOW --host-network=$HOST_NETWORK --https=$HTTPS
fi


INSTANTIATION=`./instantiation.sh`
# The generated compose file
COMPOSE_FILE="docker-compose.${INSTANTIATION}.yml"
echo "Using compose file: $COMPOSE_FILE"

# Set environment variables
export CI=true
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
echo "Running with USER_ID=$USER_ID and GROUP_ID=$GROUP_ID"

# Create necessary directories for Playwright
echo "Creating test result directories..."
mkdir -p test-results playwright-report

if [ "$HTTPS" = "true" ]; then
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
  
  docker compose -f $COMPOSE_FILE up --build --detach --remove-orphans

  # Run tests with the Playwright container
  echo "Running tests with Playwright container..."
  docker compose -f $COMPOSE_FILE run playwright
  TEST_EXIT_CODE=$?
  
  # Collect logs and shut down
  echo "Collecting logs and shutting down..."
  docker compose -f $COMPOSE_FILE logs > docker-compose.log
  docker compose -f $COMPOSE_FILE down
  
  # Exit with the test exit code
  exit $TEST_EXIT_CODE
else
  # Just run everything and keep it running
  echo "Running services without tests..."
  docker compose -f $COMPOSE_FILE up --build --remove-orphans
fi
