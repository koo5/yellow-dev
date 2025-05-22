#!/bin/bash
set -euo pipefail

# Script to run the stack in CI mode
# Generates customized docker-compose files based on parameters

# Parse arguments
HOLLOW=${1:-false}
HOST_NETWORK=${2:-false}
RUN_TESTS=${3:-true}
GENERATE=${4:-false}

if [ "$GENERATE" = "true" ]; then
  # Generate the customized docker-compose file with Dockerfiles
  echo "Generating Dockerfiles and compose file..."
  scripts/generate_compose.py --hollow=$HOLLOW --host-network=$HOST_NETWORK
fi

# Determine which compose file was generated
if [ "$HOLLOW" = "true" ]; then
  MODE="hollow"
else
  MODE="full"
fi

if [ "$HOST_NETWORK" = "true" ]; then
  NETWORK="hostnet"
else
  NETWORK="stack"
fi

# The generated compose file
COMPOSE_FILE="docker-compose.${MODE}.${NETWORK}.yml"
echo "Using compose file: $COMPOSE_FILE"

# Set environment variables
export CI=true
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)
echo "Running with USER_ID=$USER_ID and GROUP_ID=$GROUP_ID"

# Create necessary directories for Playwright
echo "Creating test result directories..."
mkdir -p test-results playwright-report

# Set up BuildX cache arguments if available
CACHE_ARGS=""
if [ -n "${BUILDX_CACHE:-}" ]; then
  echo "Using BuildX cache: $BUILDX_CACHE"
  CACHE_ARGS="--cache-from=$BUILDX_CACHE --cache-to=$BUILDX_CACHE"
  export BUILDX_CACHE_ARGS="$CACHE_ARGS"
fi

if [ "$RUN_TESTS" = "true" ]; then
  # Start services, run tests, then shut down
  echo "Running with cache args: $CACHE_ARGS"
  set -x
  
  # Use BuildX cache if available
  if [ -n "$CACHE_ARGS" ]; then
    # Build images with cache first
    docker compose -f $COMPOSE_FILE build $CACHE_ARGS
    docker compose -f $COMPOSE_FILE up --detach --remove-orphans
  else
    docker compose -f $COMPOSE_FILE up --build --detach --remove-orphans
  fi
  
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
  if [ -n "$CACHE_ARGS" ]; then
    docker compose -f $COMPOSE_FILE build $CACHE_ARGS
    docker compose -f $COMPOSE_FILE up --remove-orphans
  else
    docker compose -f $COMPOSE_FILE up --build --remove-orphans
  fi
fi
