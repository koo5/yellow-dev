# CI vs Development Environment

This document outlines the key differences between development and CI environments for the yellow-dev project, and how Docker is configured differently for each scenario.

## Development Environment

In the development environment:

1. **Volume Mounts**: 
   - Source code is bind-mounted from the host into containers
   - Node modules, build artifacts, and data directories are also bind-mounted
   - This allows for real-time code changes without rebuilding containers

2. **User Permissions**:
   - Containers run with the host's UID/GID
   - This ensures that files created inside containers have the correct ownership on the host
   - Required to avoid permission issues with bind-mounted volumes

3. **Networking**:
   - Ports are exposed to the host for direct access
   - Services can be accessed via localhost

4. **Resource Symlinks**:
   - May use symlinks to shared directories (like yellow-server-common)
   - Reduces duplication of code

## CI Environment

In the CI environment:

1. **Self-Contained Builds**:
   - No bind mounts to host filesystem
   - All source code is copied into containers during build
   - Dependencies are installed fresh inside containers
   - No need to use host's UID/GID for file permissions

2. **Build Caching**:
   - Utilizes Docker layer caching for faster builds
   - BuildKit's cache capabilities are leveraged
   - GitHub Actions cache is used to persist layers between workflow runs

3. **Fixed UIDs/GIDs**:
   - Can use fixed UID/GID values inside containers
   - No risk of permission issues across different environments

4. **No External Symlinks**:
   - All dependencies are included directly in the build
   - No symlinking to external resources

## Implementation

To handle both environments appropriately:

1. **Environment Detection**:
   - `CI=true` environment variable is set in GitHub Actions
   - This can be used to detect whether we're in CI or development mode

2. **Docker Compose Configuration**:
   - Different volume configurations based on environment
   - In CI: no bind mounts, fully containerized
   - In development: bind mounts for sources and data

3. **Build Arguments**:
   - Pass environment-specific build args to Docker
   - `IS_CI` build arg to modify Dockerfile behavior
   - Use host UID/GID in development, fixed values in CI

4. **Startup Scripts**:
   - Conditional logic in startup scripts
   - Skip symlinking in CI environment

This separation ensures optimal performance and reliability in both scenarios while maintaining a consistent application behavior.