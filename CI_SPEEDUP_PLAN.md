# CI Speedup Plan

## Dockerfile Structure Changes

1. Rename existing Dockerfiles to `Dockerfile_hollow` for each service:
   - `/yellow-client/Dockerfile` → `/yellow-client/Dockerfile_hollow`
   - `/yellow-admin/Dockerfile` → `/yellow-admin/Dockerfile_hollow`
   - `/yellow-server/Dockerfile` → `/yellow-server/Dockerfile_hollow`
   - `/yellow-server-common/Dockerfile` → `/yellow-server-common/Dockerfile_hollow`
   - `/yellow-server-module-messages/Dockerfile` → `/yellow-server-module-messages/Dockerfile_hollow`

2. Modify each hollow Dockerfile to:
   - Copy package.json and lockfiles during build
   - Install dependencies during build
   - Remain as base images that don't include source code

3. Create new non-hollow Dockerfiles that:
   - Use the hollow Dockerfiles as base images
   - Copy source code into the container
   - Don't reinstall dependencies (already in the hollow base image)

## Docker Compose Changes

1. Create script to parse `docker-compose.yml` and remove volume sections:
   - Parse the YAML file using Python's PyYAML
   - Walk through all services and remove their volume sections
   - Output a modified docker-compose file for CI use

2. Update the CI workflow to use the modified docker-compose configuration:
   - Generate the modified configuration at CI runtime
   - Use the generated config instead of the volume-based dev config

## Playwright Container

1. Create dedicated Playwright container:
   - Create a new Dockerfile for running Playwright tests
   - Include both client and admin code in the container
   - Pre-install all testing dependencies
   - Configure for headless browser testing

2. Update the test running script:
   - Launch the Playwright container instead of running tests directly
   - Pass test results back to the CI environment
   - Configure proper networking with other containers

## Caching and BuildX Configuration

1. Reintroduce BuildX caching:
   - Configure GitHub Actions to use BuildX
   - Set up proper caching between workflow runs

2. Optimize CI performance:
   - Build hollow base images first with caching
   - Build application images using the cached hollow images
   - Ensure proper layering for optimal cache utilization

## Implementation Order

1. Create and test hollow Dockerfiles
2. Create and test non-hollow Dockerfiles
3. Implement docker-compose parser script
4. Create dedicated Playwright container
5. Integrate BuildX caching
6. Update CI workflow scripts