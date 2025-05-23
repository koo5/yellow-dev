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

if [ "$HTTP" = "true" ]; then
  PROTO="http"
else
  PROTO="https"
fi

echo "${MODE}.${NETWORK}.${PROTO}"
