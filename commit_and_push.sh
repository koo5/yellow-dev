#!/bin/fish



function e; or status --is-interactive; or exit 1; end

nvm use;


# Check for commit message
if test (count $argv) -eq 0
    # No message provided, open mcedit to write one interactively
    set temp_msg_file /tmp/commit_message.txt
    set temp_msg_file2 /tmp/commit_message2.txt
    echo "# Write your commit message above. Lines starting with '#' will be ignored." > $temp_msg_file
    mcedit $temp_msg_file
    # Read the message back and strip out comments
    grep -v '^#' $temp_msg_file | string trim > $temp_msg_file2
    if test -z (cat $temp_msg_file2)
        echo "No commit message provided. Aborting."
        exit 1
    end
    set m "-F" $temp_msg_file2
else
    # Use the provided message
    set m "-m" $argv[1]
end

echo "commit message arg:" $m

git status; e

echo
echo ========
echo

cd yellow-server-common/
bun bun.lockb > bun.lockb.txt
pwd; git status;
gca $m; gp; e
cd ..
echo
echo ========
echo

cd yellow-server/src
bun bun.lockb > bun.lockb.txt
pwd; git status;
../../dev_common_link.sh; e
gca $m; gp; e
cd ../..
echo
echo ========
echo

cd yellow-server-module-messages/src
bun bun.lockb > bun.lockb.txt
pwd; git status;
../../dev_common_link.sh; e
gca $m; gp; e
cd ../..
echo
echo ========
echo

cd yellow-admin/
bun bun.lockb > bun.lockb.txt
pwd; git status;
#../dev_common_link.sh; e
gca $m; gp; e
cd ..
echo
echo ========
echo
 
cd yellow-client/
bun bun.lockb > bun.lockb.txt
pwd; git status;
gca $m; gp; e
cd ..
echo
echo ========
echo

pwd; git status;
gca $m; gp; e
git status

mpv /usr/share/sounds/freedesktop/stereo/trash-empty.oga > /dev/null
