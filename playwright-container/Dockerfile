FROM mcr.microsoft.com/playwright:v1.52.0-noble

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip xvfb

RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# Copy client and admin code
COPY ./yellow-client /app/yellow-client
COPY ./yellow-admin /app/yellow-admin

# Copy test runner script
COPY ./playwright-container/run-tests.sh /app/run-tests.sh
RUN chmod +x /app/run-tests.sh

# Install dependencies
RUN cd /app/yellow-client && bun i --frozen-lockfile
RUN cd /app/yellow-admin && bun i --frozen-lockfile

# Create test result directories
RUN mkdir -p /app/yellow-client/test-results /app/yellow-client/playwright-report
RUN mkdir -p /app/yellow-admin/test-results /app/yellow-admin/playwright-report

# Set proper permissions for test directories
RUN chmod -R 777 /app/yellow-client/test-results /app/yellow-client/playwright-report
RUN chmod -R 777 /app/yellow-admin/test-results /app/yellow-admin/playwright-report

CMD ["/app/run-tests.sh"]
