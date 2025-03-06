#!/bin/sh

bun i --frozen-lockfile
mkdir -p uploads/dating-photos/
echo -ne "\033]0;YELLOW MODULE DATING\007"
bun module-dating.js $1
