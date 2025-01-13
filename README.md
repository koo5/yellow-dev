## setup


0)
```
git submodule update --init
```
1)
```
cd yellow-server-common; bun i; cd ..
```
2)
```
docker-compose down; docker-compose up --build --remove-orphans
```
(mariadb starts)
3)

```
 ./dev_db_init.py (hostname) |  mariadb --protocol=tcp --host=localhost --user=root --password=password --force
```
4)
(full stack should be up & healthy now)

## development

* https://bun.sh/docs/runtime/debugger

```
 npm install -g git-format-staged prettier prettier-plugin-svelte
```
```
tail -f /var/snap/docker/common/var-lib-docker/volumes/yellow-dev_server_logs/_data/server.log | node node_modules/pino-pretty-min/bin.js
tail -n 9999999 -f /var/snap/docker/common/var-lib-docker/volumes/yellow-dev_server_logs/_data/json.log | pino-elasticsearch -t 100 -l trace -i logs-yellow -u elastic -p changeme -n https://localhost:9200 --rejectUnauthorized false
```
( https://github.com/sherifabdlnaby/elastdocker )




