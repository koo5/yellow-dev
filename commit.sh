#!/bin/fish

function e; or status --is-interactive; or exit 1; end

set m $argv[1]

echo $m

git status; e

cd yellow-server-common/
pwd; git status;
gcam $m; gp; e
cd ..

cd yellow-server/src
pwd; git status;
../../link.sh; e
gcam $m; gp; e
cd ../..

cd yellow-server-module-messages/src
pwd; git status;
../../link.sh; e
gcam $m; gp; e
cd ../..

cd yellow-admin/
pwd; git status;
../link.sh; e
gcam $m; gp; e
cd ..
 
cd yellow-client/
pwd; git status;
gcam $m; gp; e
cd ..

pwd; git status;
gcam $m; gp; e
git status
