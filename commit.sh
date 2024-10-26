#!/bin/fish

set m $argv[1]

echo $m

cd yellow-server-common/
pwd; git status;
gcam $m; gp
cd ..

cd yellow-server/src
pwd; git status;
../../link.sh
gcam $m; gp
cd ../..

cd yellow-server-module-messages/src
pwd; git status;
../../link.sh
gcam $m; gp
cd ../..

cd yellow-admin/
pwd; git status;
../link.sh
gcam $m; gp
cd ..
 
cd yellow-client/
pwd; git status;
gcam $m; gp
cd ..

pwd; git status;
gcam $m; gp
git status
