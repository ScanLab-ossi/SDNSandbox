#!/bin/bash
set -e

service openvswitch-switch start
SHELL="/bin/bash" PYTHONPATH="./mininet" exec python3 -m sdnsandbox -c example.config.json -o /opt