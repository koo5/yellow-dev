## Setup

1) Initialize submodules
```
git submodule update --init
```

2) Start the stack
   
For development (hollow mode with bind mounts):
```
# Generate the development configuration
python scripts/generate_compose.py --hollow=true --host-network=false

docker volume rm yellow-dev_mariadb yellow-dev_mariadb_tmp yellow-dev_server_logs yellow-dev_server_tmp

# Run the stack (passing your user ID and group ID to containers)
USER_ID=$(id -u) GROUP_ID=$(id -g) docker compose -f docker-compose.yml up --build --remove-orphans
```

For CI (full mode without bind mounts):
```
./ci-run.sh false false
```
Parameters: `./ci-run.sh [hollow] [host-network] [run-tests]`

Example usage:
- Run in CI mode with tests: `./ci-run.sh false false true`
- Run in CI mode without tests: `./ci-run.sh false false false`
- Run in development mode: `./ci-run.sh true false false`

## Docker Configuration

This project uses a dynamic approach to Docker configuration:

1. **File Structure**:
   - `docker-compose.template.yml` - Base template for compose configuration
   - `Dockerfile_template` - Base template for container configuration
   - `Dockerfile_fragment_copy` - Fragment containing COPY and package installation commands

2. **Generated Files** (by `scripts/generate_compose.py`):
   - `docker-compose.{mode}.{network}.yml` files - Generated compose files
   - `Dockerfile_hollow` - For development with bind mounts
   - `Dockerfile_full` - For CI with copied source code

3. **Modes**:
   - `hollow` - Development mode with bind mounts
   - `full` - CI mode with copied source code

4. **Networks**:
   - `stack` - Default Docker network with containers
   - `hostnet` - Host network mode

A symlink to the most recently generated docker-compose file is created as `docker-compose.yml`.

## development notes

* https://bun.sh/docs/runtime/debugger

```
tail -f /var/snap/docker/common/var-lib-docker/volumes/yellow-dev_server_logs/_data/server.log | node node_modules/pino-pretty-min/bin.js
tail -n 9999999 -f /var/snap/docker/common/var-lib-docker/volumes/yellow-dev_server_logs/_data/json.log | pino-elasticsearch -t 100 -l trace -i logs-yellow -u elastic -p changeme -n https://localhost:9200 --rejectUnauthorized false
```
( https://github.com/sherifabdlnaby/elastdocker )



### prettier
```
 npm install -g git-format-staged prettier prettier-plugin-svelte
 set -U fish_user_paths $fish_user_paths ~/node_modules/.bin/
```


### db cleanup
```
echo "use yellow_module_org_libersoft_messages; delete from messages; delete from attachments; delete from file_uploads" |  mariadb --protocol=tcp --host=localhost --user=root --password=password --force
```


### client build
```
cd yellow-client;

bun run build; rm -rf client; mv build client;  python3 -m http.server
```
