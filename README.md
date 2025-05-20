## setup


1)
```
git submodule update --init
```
2)
```
CI=true docker compose down; UID=(id -u) GID=(id -g) docker compose up --build --remove-orphans
```

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
