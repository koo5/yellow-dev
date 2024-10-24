```
mariadb --protocol=tcp --host=localhost --user=root --password=password
```
```
CREATE USER username IDENTIFIED BY 'password';
CREATE DATABASE yellow;
GRANT ALL ON yellow.* TO username;

CREATE USER 'yellow_module_org_libersoft_messages' IDENTIFIED BY 'password';
CREATE DATABASE yellow_module_org_libersoft_messages;
GRANT ALL ON yellow_module_org_libersoft_messages.* TO 'yellow_module_org_libersoft_messages';

USE yellow;
INSERT INTO admins (username, password) VALUES ('admin', '$argon2id$v=19$m=65536,t=20,p=1$Vmb9bCJSHUOJDiS+amdMkzxTljfkanX0JKsYecdBCkQ$slQjytnGeh4/ScqmXOJ6mjjfdmu/9eVSd6dV032nrm8');
INSERT INTO modules (name, connection_string) VALUES ('org.libersoft.messages', 'ws://localhost:25001/');









```


```

docker-compose down; docker-compose up --build --remove-orphans

```
