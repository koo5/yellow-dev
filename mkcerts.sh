#!/bin/sh

mkdir certs; openssl req -x509 -nodes -newkey rsa:2048 -keyout certs/server.key -out certs/server.crt -config openssl.cnf -days 365
