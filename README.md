```
mariadb --protocol=tcp --host=localhost --user=root --password=password
```
```
CREATE USER username IDENTIFIED BY 'password';
CREATE DATABASE yellow;
GRANT ALL ON yellow.* TO username;

USE yellow;
INSERT INTO admins (username, password) VALUES ('admin', 'password');
INSERT INTO modules (name, connection_string) VALUES ('org.libersoft.messages', 'ws://localhost:25001/');


CREATE USER 'yellow_module_org_libersoft_messages' IDENTIFIED BY 'password';
CREATE DATABASE yellow_module_org_libersoft_messages;
GRANT ALL ON yellow_module_org_libersoft_messages.* TO 'yellow_module_org_libersoft_messages';







```


```

docker-compose down; docker-compose up --build --remove-orphans

```
