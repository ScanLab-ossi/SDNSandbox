#!/bin/bash
set -e

service openvswitch-switch start
OUTPUT_PATH=/opt
CONF_FILE=$OUTPUT_PATH/config.json
if [ ! -f "$CONF_FILE" ] ; then
	  CONF_FILE=example.config.json
fi
SHELL="/bin/bash" PYTHONPATH="./mininet" exec python3 -m sdnsandbox -c $CONF_FILE -o $OUTPUT_PATH