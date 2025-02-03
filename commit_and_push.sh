#!/bin/fish

function e; or status --is-interactive; or exit 1; end

nvm use;

# Helper function to get a commit message from argv or open an editor
function get_commit_message
    set temp_msg_file /tmp/commit_message.txt
    set temp_msg_file2 /tmp/commit_message2.txt

    echo "argv: $argv"

    if test (count $argv) -eq 0
        echo 'No message provided, open mcedit to write one interactively'
        echo "# Write your commit message above. Lines starting with '#' will be ignored." > $temp_msg_file
        kwrite $temp_msg_file
        # Read the message back and strip out comments
        grep -v '^#' $temp_msg_file | string trim > $temp_msg_file2
        if test -z (cat $temp_msg_file2)
            echo "No commit message provided. Aborting."
            exit 1
        end
    else
        echo 'Commit message provided as argument'
        echo $argv > $temp_msg_file2
    end
    set -g commitMessage "-F $temp_msg_file2"
end

echo "argv: $argv"
get_commit_message $argv
echo "commitMessage: $commitMessage"
cat /tmp/commit_message2.txt


# Function to update all dependent repos to point to the new commit hash
function update_shared_lib_references
    # 1. Get the new commit hash from the shared library
    pushd yellow-server-common
    set newHash (git rev-parse HEAD | string trim)
    echo "current hash for yellow-server-common: $newHash"
    popd

    # 2. Update each dependent repo
    set dependentRepos \
        "yellow-server/src" \
        "yellow-server-module-messages/src"

    for repo in $dependentRepos
        echo "checking dependency in $repo"
        pushd $repo

        jq --arg commit "$newHash" '
          .dependencies["yellow-server-common"] =
          "git+https://github.com/libersoft-org/yellow-server-common#\($commit)"
        ' package.json > package.tmp

        if diff package.json package.tmp
            echo "No changes to package.json"
            rm package.tmp
            popd
            continue
        end

        mv package.tmp package.json

        bun i

        # Commit & push
        git add package.json
        git add package-lock.json
        git add bun.lock
        git commit -m "bump yellow-server-common to commit $newHash"

        popd
    end
end


git status; e

echo
echo ========
echo


cd yellow-server-common/
pwd; git status;
fish -c "git commit -a $commitMessage"; gp; e
cd ..


cd yellow-server/src
#bun bun.lockb > bun.lockb.txt
pwd; git status;
../../dev_common_link.sh; e
fish -c "git commit -a $commitMessage"; gp; e
cd ../..

echo
echo ========
echo

cd yellow-server-module-messages/src
pwd; git status;
../../dev_common_link.sh; e
fish -c "git commit -a $commitMessage"; gp; e
cd ../..

echo
echo ========
echo

cd yellow-admin/
pwd; git status;
#../dev_common_link.sh; e
fish -c "git commit -a $commitMessage"; gp; e
cd ..

echo
echo ========
echo
 
cd yellow-client/
pwd; git status;
fish -c "git commit -a $commitMessage"; gp; e
cd ..

echo
echo ========
echo
update_shared_lib_references
echo
echo ========
echo

pwd; git status;
echo
echo ========
echo
fish -c "git commit -a $commitMessage"; gp; e
git status

mpv /usr/share/sounds/freedesktop/stereo/trash-empty.oga > /dev/null
