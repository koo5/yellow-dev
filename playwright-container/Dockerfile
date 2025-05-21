FROM mcr.microsoft.com/playwright:v1.41.1-jammy

# Use USER_ID and GROUP_ID passed from environment
ARG USER_ID=1000
ARG GROUP_ID=1000

# Set working directory
WORKDIR /app

# Copy client and admin code
COPY ./yellow-client /app/yellow-client
COPY ./yellow-admin /app/yellow-admin

# Install dependencies for client
WORKDIR /app/yellow-client
RUN npm install --force

# Install Playwright browsers
RUN npx playwright install --with-deps

# Set up proper networking
ENV CI=true

# Create a user with the provided USER_ID/GROUP_ID for running tests
RUN if getent group $GROUP_ID > /dev/null; then \
        GROUP_NAME=$(getent group $GROUP_ID | cut -d: -f1); \
    else \
        groupadd -r -g $GROUP_ID playwright_group && GROUP_NAME=playwright_group; \
    fi && \
    if getent passwd $USER_ID > /dev/null; then \
        USER_NAME=$(getent passwd $USER_ID | cut -d: -f1); \
    else \
        useradd -r -u $USER_ID -g $GROUP_NAME -G audio,video playwright && USER_NAME=playwright; \
    fi && \
    mkdir -p /home/$USER_NAME && \
    chown -R $USER_ID:$GROUP_ID /home/$USER_NAME && \
    chown -R $USER_ID:$GROUP_ID /app
USER $USER_ID:$GROUP_ID

# Default command - can be overridden by docker-compose
CMD ["npx", "playwright", "test", "--reporter=line,github"]