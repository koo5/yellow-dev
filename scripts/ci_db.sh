#!/usr/bin/env fish

./dev_db_init.py (hostname) |  mariadb --protocol=tcp --host=localhost --user=root --password=password --force
./dev_db_populate.py (hostname) |  mariadb --protocol=tcp --host=localhost --user=root --password=password --force
