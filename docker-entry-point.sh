#!/bin/bash
set -e

service openvswitch-switch start
PYTHONPATH=$PYTHONPATH;./mininet python3  -m sdnsandbox -c example.config.json -o /opt