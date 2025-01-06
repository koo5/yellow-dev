#!/bin/fish

function e; or status --is-interactive; or exit 1; end

nvm use;

set m $argv[1]

echo $m

git status; e

echo
echo ========
echo

cd yellow-server-common/
bun bun.lockb > bun.lockb.txt
pwd; git status;
gcam $m; gp; e
cd ..
echo
echo ========
echo

cd yellow-server/src
bun bun.lockb > bun.lockb.txt
pwd; git status;
../../dev_common_link.sh; e
gcam $m; gp; e
cd ../..
echo
echo ========
echo

cd yellow-server-module-messages/src
bun bun.lockb > bun.lockb.txt
pwd; git status;
../../dev_common_link.sh; e
gcam $m; gp; e
cd ../..
echo
echo ========
echo

cd yellow-admin/
bun bun.lockb > bun.lockb.txt
pwd; git status;
#../dev_common_link.sh; e
gcam $m; gp; e
cd ..
echo
echo ========
echo
 
cd yellow-client/
bun bun.lockb > bun.lockb.txt
pwd; git status;
gcam $m; gp; e
cd ..
echo
echo ========
echo

pwd; git status;
gcam $m; gp; e
git status

mpv /usr/share/sounds/Oxygen-Im-New-Mail.ogg > /dev/null
