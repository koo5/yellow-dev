#!/bin/sh

screen -dmS yellow-server-module-dating bash -c ". ./colors.sh; trap bash SIGINT; (./start-hot.sh ; bash);"
