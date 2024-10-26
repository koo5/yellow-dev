#!/usr/bin/env fish

function e; or status --is-interactive; or exit 1; end

nvm use; e; bun remove yellow-server-common; e; bun add https://github.com/libersoft-org/yellow-server-common --latest; e; rm -rf ./node_modules/yellow-server-common; ln -s ../../../yellow-server-common ./node_modules/yellow-server-common; e

