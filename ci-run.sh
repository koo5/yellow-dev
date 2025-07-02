#!/bin/bash
set -euo pipefail

# Script to run the stack in CI mode
# Generates customized docker-compose files based on parameters
#
# Usage: ./ci-run.sh [HOLLOW] [HOST_NETWORK] [HTTP] [RUN_TESTS] [GENERATE] [DOWN_FIRST] [CLEAN] [LOOP]
#
# Parameters:
#   HOLLOW (default: false)      - Use hollow build (true/false)
#   HOST_NETWORK (default: false) - Use host networking (true/false)
#   HTTP (default: true)         - Use HTTP instead of HTTPS (true/false)
#   RUN_TESTS (default: true)    - Run Playwright tests (true/false)
#   GENERATE (default: true)     - Generate compose files (true/false)
#   DOWN_FIRST (default: false)  - Bring down existing stack first (true/false)
#   CLEAN (default: false)       - Run clean.py before starting (true/false)
#   LOOP (default: empty)        - Run services in a loop (any non-empty value enables)
#
# Example: ./ci-run.sh false false true true true true true

# Parse arguments
HOLLOW=${1:-false}
HOST_NETWORK=${2:-false}
HTTP=${3:-true}
RUN_TESTS=${4:-true}
GENERATE=${5:-true}
DOWN_FIRST=${6:-false}
CLEAN=${7:-false}
LOOP=${8:-}

# Set environment variables and determine compose file name
export HOLLOW
export HOST_NETWORK
export HTTP
INSTANTIATION=`./instantiation.sh`
COMPOSE_FILE="generated/docker-compose.${INSTANTIATION}.yml"

# Bring down existing stack if requested
if [ "$DOWN_FIRST" = "true" ]; then
  echo "Bringing down existing stack..."

  if [ -f "last.yaml" ]; then
    echo "Found last.yaml, using it to bring down the previous stack"
    set +e
    docker compose --project-directory . -f last.yaml down
    set -e
  else
    echo "No last.yaml found, trying to determine compose file from current parameters"
    if [ -f "$COMPOSE_FILE" ]; then
      echo "Using compose file: $COMPOSE_FILE"
      set +e
      docker compose --project-directory . -f $COMPOSE_FILE down
      set -e
    fi
  fi
fi

# Clean up if requested
if [ "$CLEAN" = "true" ]; then
  echo "Running clean.py..."
  ./clean.py
fi

if [ "$GENERATE" = "true" ]; then
  # Generate the customized docker-compose file with Dockerfiles
  echo "Generating Dockerfiles and compose file..."
  scripts/generate_compose.py --hollow=$HOLLOW --host-network=$HOST_NETWORK --http=$HTTP
fi
echo "Using compose file: $COMPOSE_FILE"

# Set environment variables
#export CI=true
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



# Copy current compose file to last.yaml for future reference
echo "Copying $COMPOSE_FILE to last.yaml..."
cp "$COMPOSE_FILE" last.yaml


if [ "$RUN_TESTS" = "true" ]; then
  # Start services, run tests, then shut down

  # Time the stack startup
  echo "[CI-RUN] Starting stack..."
  STACK_START_TIME=$(date +%s)
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE --parallel 1 up --build --remove-orphans --force-recreate --detach
  set +x
  STACK_END_TIME=$(date +%s)
  STACK_DURATION=$((STACK_END_TIME - STACK_START_TIME))
  echo "[CI-RUN] Stack startup completed in ${STACK_DURATION} seconds"

  # Run tests with the Playwright container
  echo "[CI-RUN] Running tests with Playwright container..."
  PLAYWRIGHT_START_TIME=$(date +%s)
  set +e
  set -x
  docker compose --project-directory . -f $COMPOSE_FILE --parallel 1 run --build playwright

  TEST_EXIT_CODE=$?

  ls -la /app/yellow-client/test-results || true
  ls -la /app/yellow-client/playwright-report || true

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

  if test -z "$LOOP"; then
	echo "Running services without tests..."
	set -x
	./clean.py
	docker compose --project-directory . -f $COMPOSE_FILE up --build --remove-orphans
	set +x
  fi

  while test -n "$LOOP"; do
	  echo "Running services without tests..."
	  set -x
	  ./clean.py
	  docker compose --project-directory . -f $COMPOSE_FILE up --build --remove-orphans
	  set +x
  done

fi
