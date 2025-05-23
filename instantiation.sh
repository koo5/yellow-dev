#!/bin/bash

if [ "$HOLLOW" = "true" ]; then
  MODE="hollow"
else
  MODE="full"
fi

if [ "$HOST_NETWORK" = "true" ]; then
  NETWORK="hostnet"
else
  NETWORK="stack"
fi

if [ "$HTTPS" = "true" ]; then
  PROTO="https"
else
  PROTO="http"
fi

echo "${MODE}.${NETWORK}.${PROTO}"
