```
 mariadb --protocol=tcp --host=localhost --user=root --password=password
```
```
CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';
CREATE DATABASE yellow;
GRANT ALL ON yellow.* TO 'username'@'localhost';
















```