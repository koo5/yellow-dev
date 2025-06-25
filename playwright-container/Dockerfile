FROM mcr.microsoft.com/playwright:v1.53.1-noble

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip xvfb

RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Copy client, admin and stack test code
COPY ./yellow-client /app/yellow-client
COPY ./yellow-admin /app/yellow-admin
COPY ./stack_tests /app/stack_tests

# Copy test runner script
COPY ./playwright-container/run-tests.sh /app/run-tests.sh
RUN chmod +x /app/run-tests.sh

# Install dependencies
RUN cd /app/yellow-client && bun i --frozen-lockfile
RUN cd /app/yellow-admin && bun i --frozen-lockfile
RUN cd /app/stack_tests && bun i --frozen-lockfile

# Create test result directories
RUN mkdir -p /app/yellow-client/test-results /app/yellow-client/playwright-report
RUN mkdir -p /app/yellow-admin/test-results /app/yellow-admin/playwright-report
RUN mkdir -p /app/stack_tests/test-results /app/stack_tests/playwright-report

# Set proper permissions for test directories
RUN chmod -R 777 /app/yellow-client/test-results /app/yellow-client/playwright-report
RUN chmod -R 777 /app/yellow-admin/test-results /app/yellow-admin/playwright-report
RUN chmod -R 777 /app/stack_tests/test-results /app/stack_tests/playwright-report

CMD ["/app/run-tests.sh"]
