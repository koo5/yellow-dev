#!/bin/bash
set -e

echo "==============================================="
echo "PLAYWRIGHT RUN-TESTS SCRIPT STARTED"
echo "==============================================="
echo "Script: /app/run-tests.sh"
echo "Time: $(date)"
echo "User: $(whoami)"
echo "Working directory: $(pwd)"
echo "==============================================="

# Start Xvfb for X11 clipboard support
echo "Starting Xvfb for X11 support..."
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
XVFB_PID=$!
sleep 2

# Show environment variables for debugging
echo "Environment:"
env | grep PLAYWRIGHT || true
echo "DISPLAY=$DISPLAY"

# Test configuration
RUN_CLIENT_TESTS=${RUN_CLIENT_TESTS:-true}
RUN_ADMIN_TESTS=${RUN_ADMIN_TESTS:-false}
RUN_STACK_TESTS=${RUN_STACK_TESTS:-false}

echo "Test configuration:"
echo "RUN_CLIENT_TESTS: $RUN_CLIENT_TESTS"
echo "RUN_ADMIN_TESTS: $RUN_ADMIN_TESTS"
echo "RUN_STACK_TESTS: $RUN_STACK_TESTS"

# Set up reporters
if [ "$CI" = "true" ]; then
  REPORTERS="--reporter=github,list,html"
else
  REPORTERS="--reporter=list,html"
fi

# Initialize exit code
TEST_EXIT_CODE=0

# Run client tests if enabled
if [ "$RUN_CLIENT_TESTS" = "true" ]; then
  echo "==============================================="
  echo "RUNNING CLIENT TESTS"
  echo "==============================================="

  # Wait for client service to be ready
  echo "Waiting for client to be ready..."
  until curl --insecure -L -s $PLAYWRIGHT_CLIENT_URL/#health > /dev/null 2>&1; do
    echo "Waiting for client..."
    sleep 2
  done
  echo "Client is ready!"

  # Change to client directory and run tests
  cd /app/yellow-client
  echo "Running client Playwright tests..."
  npx playwright test \
    --project=chromium \
    --project="Mobile Chrome" \
    --timeout 900000 \
    --retries 4 \
    $REPORTERS

  CLIENT_EXIT_CODE=$?
  if [ $CLIENT_EXIT_CODE -ne 0 ]; then
    TEST_EXIT_CODE=$CLIENT_EXIT_CODE
    echo "Client tests failed with exit code: $CLIENT_EXIT_CODE"
  else
    echo "Client tests passed!"
  fi
fi

# Run admin tests if enabled
if [ "$RUN_ADMIN_TESTS" = "true" ]; then
  echo "==============================================="
  echo "RUNNING ADMIN TESTS"
  echo "==============================================="

  # Wait for admin service to be ready
  ADMIN_URL=${PLAYWRIGHT_ADMIN_URL:-http://admin:4000}
  echo "Waiting for admin to be ready at $ADMIN_URL..."
  until curl --insecure -L -s $ADMIN_URL/health > /dev/null 2>&1; do
    echo "Waiting for admin..."
    sleep 2
  done
  echo "Admin is ready!"

  # Change to admin directory and run tests
  cd /app/yellow-admin
  echo "Running admin Playwright tests..."
  npx playwright test --project=chromium $REPORTERS

  ADMIN_EXIT_CODE=$?
  if [ $ADMIN_EXIT_CODE -ne 0 ]; then
    TEST_EXIT_CODE=$ADMIN_EXIT_CODE
    echo "Admin tests failed with exit code: $ADMIN_EXIT_CODE"
  else
    echo "Admin tests passed!"
  fi
fi

# Run stack tests if enabled
if [ "$RUN_STACK_TESTS" = "true" ]; then
  echo "==============================================="
  echo "RUNNING STACK INTEGRATION TESTS"
  echo "==============================================="

  # Wait for both admin and client services to be ready
  ADMIN_URL=${PLAYWRIGHT_ADMIN_URL:-http://admin:4000}
  echo "Waiting for admin to be ready at $ADMIN_URL..."
  until curl --insecure -L -s $ADMIN_URL/health > /dev/null 2>&1; do
    echo "Waiting for admin..."
    sleep 2
  done
  echo "Admin is ready!"

  echo "Waiting for client to be ready..."
  until curl --insecure -L -s $PLAYWRIGHT_CLIENT_URL/#health > /dev/null 2>&1; do
    echo "Waiting for client..."
    sleep 2
  done
  echo "Client is ready!"

  # Change to stack_tests directory and run tests
  cd /app/stack_tests
  echo "Running stack integration Playwright tests..."
  npx playwright test $REPORTERS

  STACK_EXIT_CODE=$?
  if [ $STACK_EXIT_CODE -ne 0 ]; then
    TEST_EXIT_CODE=$STACK_EXIT_CODE
    echo "Stack tests failed with exit code: $STACK_EXIT_CODE"
  else
    echo "Stack tests passed!"
  fi
fi

echo "Test exit code: $TEST_EXIT_CODE"

# List test results for debugging
echo "Listing test-results:"
ls -la /app/yellow-client/test-results || true
ls -la /app/yellow-admin/test-results || true
ls -la /app/stack_tests/test-results || true

echo "Listing playwright-report:"
ls -la /app/yellow-client/playwright-report || true
ls -la /app/yellow-admin/playwright-report || true
ls -la /app/stack_tests/playwright-report || true

echo "Playwright finished."

# Kill Xvfb
if [ ! -z "$XVFB_PID" ]; then
  echo "Stopping Xvfb..."
  kill $XVFB_PID 2>/dev/null || true
fi

# Exit with the test exit code
exit $TEST_EXIT_CODE
