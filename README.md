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
https://bun.sh/docs/runtime/debugger


