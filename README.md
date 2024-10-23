```
 mariadb --protocol=tcp --host=localhost --user=root --password=password
```
```
CREATE USER username IDENTIFIED BY 'password';
CREATE DATABASE yellow;
GRANT ALL ON yellow.* TO 'username'@'localhost';














```