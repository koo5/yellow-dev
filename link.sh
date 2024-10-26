#!/usr/bin/env fish

nvm use; bun remove yellow-server-common;  bun add https://github.com/libersoft-org/yellow-server-common --latest; rm -rf ./node_modules/yellow-server-common; ln -s ../../../yellow-server-common ./node_modules/yellow-server-common
