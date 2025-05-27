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
  
  # Time the stack startup
  echo "[CI-RUN] Starting stack..."
  STACK_START_TIME=$(date +%s)
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE up --build --remove-orphans --force-recreate --detach
  set +x
  STACK_END_TIME=$(date +%s)
  STACK_DURATION=$((STACK_END_TIME - STACK_START_TIME))
  echo "[CI-RUN] Stack startup completed in ${STACK_DURATION} seconds"

  # Run tests with the Playwright container
  echo "[CI-RUN] Running tests with Playwright container..."
  PLAYWRIGHT_START_TIME=$(date +%s)
  set +e
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE run --build playwright /app/run-tests.sh

  TEST_EXIT_CODE=$?
  set +x
  set -e
  PLAYWRIGHT_END_TIME=$(date +%s)
  PLAYWRIGHT_DURATION=$((PLAYWRIGHT_END_TIME - PLAYWRIGHT_START_TIME))
  echo "[CI-RUN] Playwright tests completed in ${PLAYWRIGHT_DURATION} seconds"

  # Print timing summary
  TOTAL_DURATION=$((PLAYWRIGHT_END_TIME - STACK_START_TIME))
  echo "[CI-RUN] ===== TIMING SUMMARY ====="
  echo "[CI-RUN] Stack startup: ${STACK_DURATION}s"
  echo "[CI-RUN] Playwright tests: ${PLAYWRIGHT_DURATION}s"
  echo "[CI-RUN] Total time: ${TOTAL_DURATION}s"
  echo "[CI-RUN] ========================="

  # Collect logs and shut down
  echo "[CI-RUN] Collecting logs and shutting down..."
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE logs > docker-compose.log
  docker compose --project-directory . -f $COMPOSE_FILE down
  set +x
  
  # Exit with the test exit code
  exit $TEST_EXIT_CODE
else
  # Just run everything and keep it running
  echo "Running services without tests..."
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE up --build --remove-orphans
  set +x
fi
