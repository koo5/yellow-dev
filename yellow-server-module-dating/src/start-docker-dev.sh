#!/bin/sh

mkdir -p uploads/message-attachments/

#[ ! -d "./node_modules/" ] &&
bun i --frozen-lockfile
rm -rf ./node_modules/yellow-server-common; ln -s ../../../yellow-server-common ./node_modules/yellow-server-common
bun app.ts --create-database
bun --watch app.ts
