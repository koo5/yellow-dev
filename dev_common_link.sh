#!/usr/bin/env fish

function e; or status --is-interactive; or exit 1; end

rm -rf ./node_modules/yellow-server-common;
ln -s ../../../yellow-server-common ./node_modules/yellow-server-common; e;
