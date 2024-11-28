#!/bin/sh

bun server.js $1 | ./node_modules/pino-mysql/pino-mysql -c ./pino-mysql-database-config.json
