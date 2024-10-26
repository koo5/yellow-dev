#!/bin/fish

set m $argv[1]

echo $m

cd yellow-server-common/
gcam $m; gp
cd ..

cd yellow-server/src
nvm use; bun remove yellow-server-common;  bun add https://github.com/libersoft-org/yellow-server-common --latest; bun link yellow-server-common
gcam $m; gp
cd ../..

cd yellow-server-module-messages/src
nvm use; bun remove yellow-server-common;  bun add https://github.com/libersoft-org/yellow-server-common --latest; bun link yellow-server-common
gcam $m; gp
cd ../..

cd yellow-admin/
nvm use; bun remove yellow-server-common;  bun add https://github.com/libersoft-org/yellow-server-common --latest; bun link yellow-server-common
gcam $m; gp
cd ..
 
cd yellow-client/
gcam $m; gp
cd ..

gcam $m; gp
