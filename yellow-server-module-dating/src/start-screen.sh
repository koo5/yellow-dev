#!/bin/sh

bun i --frozen-lockfile
screen -dmS yellow-module-dating bash -c '
echo -ne "\033]0;YELLOW MODULE DATING\007"
while true; do
 bun module-dating.js || exit 1
done
'
