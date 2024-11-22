## setup


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

```
nvm use; bun remove yellow-server-common;  bun add https://github.com/libersoft-org/yellow-server-common --latest; rm -rf ./node_modules/yellow-server-common; ln -s ../../../yellow-server-common ./node_modules/yellow-server-common

```
https://bun.sh/docs/runtime/debugger


