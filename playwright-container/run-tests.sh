#!/bin/bash
set -e

echo "Playwright run-tests starting..."

# Show environment variables for debugging
echo "Environment:"
env | grep PLAYWRIGHT || true

# Wait for client service to be ready
echo "Waiting for client to be ready..."
until curl --insecure -L -s $PLAYWRIGHT_CLIENT_URL/#health > /dev/null 2>&1; do
  echo "Waiting for client..."
  sleep 2
done
echo "Client is ready!"

# Change to client directory
cd /app/yellow-client

# Run playwright tests with appropriate reporter
if [ "$CI" = "true" ]; then
  REPORTERS="--reporter=github,list,html"
else
  REPORTERS="--reporter=list,html"
fi

echo "Running Playwright tests..."
npx playwright test \
  --timeout 100000 \
  src/modules/org.libersoft.messages/tests/e2e/everything.test.ts \
  $REPORTERS

# Capture exit code
TEST_EXIT_CODE=$?

echo "Test exit code: $TEST_EXIT_CODE"

# List test results for debugging
echo "Listing test-results:"
ls -la /app/yellow-client/test-results || true

echo "Listing playwright-report:"
ls -la /app/yellow-client/playwright-report || true

echo "Playwright finished."

# Exit with the test exit code
exit $TEST_EXIT_CODE